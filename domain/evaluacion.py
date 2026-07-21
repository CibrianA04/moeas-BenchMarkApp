# -*- coding: utf-8 -*-
"""
Evaluacion por lotes: corre los indicadores elegidos sobre TODAS las corridas
cargadas y devuelve los valores POR CORRIDA, agrupados para comparar.

Esta capa NO calcula medias, desviaciones ni pruebas estadisticas: eso es de
`domain/statistics.py`

Escenario = (MOP, m, N). N = tamano de poblacion. Todas las corridas
de un mismo escenario comparten UN frente de referencia y UN punto de referencia
de HV, para que sus valores sean comparables entre si.

Politica del punto de referencia de HV (nadir / margen sobre el rango / fijo): es
una eleccion de INGENIERIA para hacer comparables las corridas
}El modo default "nadir_x1.1" calcula en realidad
nadir + 0.1*(nadir - ideal): un margen del 10% del RANGO por objetivo, robusto al
signo (multiplicar el nadir por 1.1 literal, con objetivos NEGATIVOS como
VNT2/VNT3, desplazaba el punto en el sentido EQUIVOCADO quedaba dominado y
HV = 0). Equivale a nadir*1.1 solo si ideal = 0 en cada objetivo. La clave del
modo conserva su nombre historico para no romper llamadas ni el mapeo de la UI.
"""
from __future__ import annotations

from typing import Callable

import numpy as np

from data import csv_io

from . import indicators
from .model import PFA

# Modos admitidos para el punto de referencia de HV.
HV_MODOS = ("nadir", "nadir_x1.1", "fijo")


def _punto_hv(grupo: list[PFA], hv_modo: str, hv_punto_fijo, m: int) -> np.ndarray:
    """
    Punto de referencia de HV para UN escenario (uno solo para todas sus corridas).

    - "nadir":      nadir (max por objetivo) sobre la UNION de todos los puntos del
                    escenario (todas las corridas y todos los MOEAs).
    - "nadir_x1.1": nadir + 0.1*(nadir - ideal) sobre esa union (DEFAULT): margen
                    del 10% del RANGO por objetivo, robusto al signo (con objetivos
                    negativos el nadir*1.1 literal quedaba dominado y HV = 0).
                    Equivale a nadir*1.1 solo si ideal = 0. Politica PENDIENTE de
                    confirmar con el doc; la clave conserva su nombre historico
                    (renombrarla es opcional/futuro).
    - "fijo":       usa `hv_punto_fijo` (vector de longitud m).
    """
    if hv_modo == "fijo":
        pf = np.asarray(hv_punto_fijo, dtype=float).ravel()
        if pf.shape != (m,):
            raise ValueError(
                f"hv_punto_fijo debe tener longitud m={m}; recibio forma {pf.shape}."
            )
        return pf

    union = np.vstack([np.asarray(p.puntos, dtype=float) for p in grupo])
    nadir = union.max(axis=0)
    if hv_modo == "nadir_x1.1":
        # Margen del 10% del rango: el offset es >= 0 en cada componente
        # (nadir - ideal >= 0), asi el punto domina al nadir con o sin negativos.
        ideal = union.min(axis=0)
        return nadir + 0.1 * (nadir - ideal)
    return nadir


def evaluar(pfas: list[PFA], indicadores_ids: list[str],
            override: dict[tuple[str, int], np.ndarray] | None = None,
            hv_modo: str = "nadir_x1.1", hv_punto_fijo=None,
            progreso: Callable[[int, int, str], None] | None = None,
            ) -> tuple[list[dict], list[dict]]:
    """
    Calcula los indicadores `indicadores_ids` sobre cada corrida de `pfas`.

    Parametros
    - pfas: lista de PFA ya cargados (dataclass de `domain.model`).
    - indicadores_ids: ids del CATALOGO de `domain.indicators` a calcular.
    - override: {(MOP, m): puntos} de frentes subidos por el usuario. Se pasa TAL
      CUAL a `csv_io.leer_frente_referencia` (opcion A: el del usuario gana). None
      por defecto.
    - hv_modo / hv_punto_fijo: politica del punto de referencia de HV (ver `_punto_hv`).
    - progreso: callback OPCIONAL (hecho, total, etiqueta), invocado UNA vez al
      INICIO de cada escenario. La UI inyecta aqui su barra de progreso; este
      modulo sigue headless (no importa streamlit).

    Devuelve (resultados, omitidos):
    - resultados: lista de dicts {mop, m, N, moea, indicador, valores:[...por corrida...]}.
      Los `valores` van ordenados por numero de corrida. Una fila por
      (MOP, m, N, MOEA, indicador); solo se emite si tiene al menos un valor.
    - omitidos: reporte de lo que NO se calculo, sin abortar el lote:
      * {"tipo": "sin_referencia", mop, m, N, indicadores_omitidos, motivo}
        (el escenario no tiene frente de referencia: se omiten SOLO los indicadores
        con requiere_ref; HV y demas sin-ref si se calculan).
      * {"tipo": "corrida_fallida", mop, m, N, moea, indicador, corrida, archivo, motivo}
        (calcular() truena en esa corrida: se omite ESA corrida y se reporta).
    """
    # Validaciones de USO (fallan rapido; no son "una corrida mala").
    if hv_modo not in HV_MODOS:
        raise ValueError(f"hv_modo invalido: '{hv_modo}'. Use uno de {HV_MODOS}.")
    desconocidos = [i for i in indicadores_ids if i not in indicators.CATALOGO]
    if desconocidos:
        raise ValueError(f"Indicadores desconocidos: {desconocidos}.")
    if hv_modo == "fijo" and "HV" in indicadores_ids and hv_punto_fijo is None:
        raise ValueError("hv_modo='fijo' requiere hv_punto_fijo (vector de longitud m).")

    # Agrupar por escenario (MOP, m, N), preservando el orden de aparicion.
    escenarios: dict[tuple[str, int, int], list[PFA]] = {}
    for p in pfas:
        escenarios.setdefault((p.mop, p.m, p.n), []).append(p)

    calcula_hv = "HV" in indicadores_ids
    ids_requiere_ref = [i for i in indicadores_ids
                        if indicators.CATALOGO[i].requiere_ref]

    resultados: list[dict] = []
    omitidos: list[dict] = []

    total_escenarios = len(escenarios)
    for idx, ((mop, m, n), grupo) in enumerate(escenarios.items()):
        if progreso is not None:
            progreso(idx, total_escenarios, f"{mop} · m={m} · N={n}")

        # Frente de referencia: UNO por escenario (solo si hace falta;
        #    csv_io lo cachea por ruta, asi que repetir MOP no reparsea).
        frente = None
        if ids_requiere_ref:
            try:
                frente = csv_io.leer_frente_referencia(mop, m, override=override)
            except Exception as exc:  # noqa: BLE001
                # FileNotFoundError es el caso esperado (no existe el frente exacto);
                # cualquier otro problema de referencia tambien deja el escenario
                # SIN-REFERENCIA en vez de abortar el lote.
                omitidos.append({
                    "tipo": "sin_referencia", "mop": mop, "m": m, "N": n,
                    "indicadores_omitidos": list(ids_requiere_ref),
                    "motivo": str(exc),
                })

        # Punto de referencia de HV: UNO por escenario (mismo para todas las corridas).
        punto_hv = _punto_hv(grupo, hv_modo, hv_punto_fijo, m) if calcula_hv else None

        # Indicadores a intentar aqui: si no hay frente, se omiten los requiere_ref.
        ids_escenario = [
            i for i in indicadores_ids
            if not (indicators.CATALOGO[i].requiere_ref and frente is None)
        ]

        # Evaluadores basados en referencia: UNA construccion por escenario
        #     (construir IGD(ref) por corrida re-procesaba el frente completo;
        #     Dp ademas comparte el mismo objeto IGD). HV y los sin-referencia
        #     siguen por calcular().
        ids_con_ref = [i for i in ids_escenario
                       if indicators.CATALOGO[i].requiere_ref]
        evaluadores = (indicators.preparar_indicadores(ids_con_ref, frente)
                       if ids_con_ref else {})

        # 3) Por MOEA (orden de aparicion), por indicador -> valores por corrida.
        por_moea: dict[str, list[PFA]] = {}
        for p in grupo:
            por_moea.setdefault(p.moea, []).append(p)

        for moea, corridas in por_moea.items():
            corridas_ord = sorted(corridas, key=lambda p: p.corrida)
            for ind_id in ids_escenario:
                valores: list[float] = []
                for p in corridas_ord:
                    try:
                        if ind_id in evaluadores:           # reusables (con ref)
                            v = evaluadores[ind_id](p.puntos)
                        else:                               # HV / sin referencia
                            v = indicators.calcular(
                                ind_id, p.puntos, ref=frente, punto_ref=punto_hv)
                    except Exception as exc:  # noqa: BLE001 una corrida mala no aborta
                        omitidos.append({
                            "tipo": "corrida_fallida", "mop": mop, "m": m, "N": n,
                            "moea": moea, "indicador": ind_id, "corrida": p.corrida,
                            "archivo": p.archivo, "motivo": str(exc),
                        })
                        continue
                    valores.append(float(v))
                if valores:
                    resultados.append({
                        "mop": mop, "m": m, "N": n, "moea": moea,
                        "indicador": ind_id, "valores": valores,
                    })

    return resultados, omitidos
