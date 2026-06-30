# -*- coding: utf-8 -*-
"""
Indicadores de calidad: catalogo + interfaz de calculo (STUB).

Pareto-compliance es un atributo de PRIMERA CLASE: solo los indicadores
compliant (estricta/debil) permiten conclusiones fuertes. HV e IGD+ lo son;
IGD, GD, MS no.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import preprocessing


@dataclass(frozen=True)
class MetaIndicador:
    id: str
    nombre: str          # texto para mostrar en la UI
    sentido: str         # "max" (mayor mejor) | "min" (menor mejor)
    requiere_ref: bool   # necesita frente de referencia
    compliance: str      # "estricta" | "debil" | "no"
    grupo: str           # "principal" | "secundario"
    descripcion: str = ""


# Catalogo. Punto de EXTENSION: agregar un indicador = agregar una entrada aqui
# (y, en la version real, su rama en calcular()).
CATALOGO: dict[str, MetaIndicador] = {
    "HV":    MetaIndicador("HV", "HV (Hypervolume)", "max", False, "strict", "principal",
                           "Volumen dominado respecto a un punto de referencia."),
    "IGD":   MetaIndicador("IGD", "IGD (Inverted Generational Distance)", "min", True, "no", "principal",
                           "Distancia media del frente de referencia al PFA."),
    "IGD+":  MetaIndicador("IGD+", "IGD+ (IGD modificado)", "min", True, "weak", "principal",
                           "Variante de IGD"),
    "R2":    MetaIndicador("R2", "R2", "min", True, "weak", "principal",
                           ""),
    "Dp":    MetaIndicador("Dp", "Delta p", "min", True, "no", "principal",
                           "Distancia de Hausdorff promediada (combina GD e IGD)."),
    "Eps+":  MetaIndicador("Eps+", "Epsilon+ (aditivo)", "min", True, "weak", "principal",
                           "Minimo desplazamiento aditivo para dominar la referencia."),
    "Riesz": MetaIndicador("Riesz", "Riesz s-energy", "min", False, "no", "secundario",
                           "Energia de pares: mide uniformidad de la distribucion."),
    "SPD":   MetaIndicador("SPD", "Solow-Polasky (SPD)", "max", False, "no", "secundario",
                           "Diversidad del conjunto de soluciones."),
}


def principales() -> list[MetaIndicador]:
    return [m for m in CATALOGO.values() if m.grupo == "principal"]


def secundarios() -> list[MetaIndicador]:
    return [m for m in CATALOGO.values() if m.grupo == "secundario"]


def calcular(ind_id: str, puntos: np.ndarray,
             ref: np.ndarray | None = None,
             punto_ref: np.ndarray | None = None, **params) -> float:
    """
    Calcula UN indicador sobre un PFA. Hoy SOLO esta implementado HV.

    - Valida `requiere_ref` contra el CATALOGO: si el indicador necesita frente de
      referencia y `ref is None`, lanza ValueError.
    - HV: via pymoo. Usa `punto_ref` (punto de referencia/nadir); si es None, se
      toma el nadir del propio conjunto (la POLITICA del punto de referencia
      —nadir, 1.1*nadir, [2,..]— esta PENDIENTE de confirmar con el doc).
    - El resto de indicadores (IGD/IGD+/R2/Dp/Eps+/Riesz/SPD) aun NO estan
      implementados: lanzan NotImplementedError.
    """
    _ = params  # reservado para parametros por indicador (futuro)
    if ind_id not in CATALOGO:
        raise KeyError(f"Indicador desconocido: '{ind_id}'.")
    meta = CATALOGO[ind_id]
    if meta.requiere_ref and ref is None:
        raise ValueError(
            f"El indicador '{ind_id}' requiere un frente de referencia (ref)."
        )

    if ind_id == "HV":
        if punto_ref is None:
            _, punto_ref = preprocessing.estimar_ideal_nadir(np.asarray(puntos, float))
        return _hv_pymoo(puntos, punto_ref)

    raise NotImplementedError(
        f"El computo de '{ind_id}' aun no esta implementado (hoy solo HV)."
    )


def _hv_pymoo(puntos: np.ndarray, punto_ref: np.ndarray) -> float:
    """
    Hypervolume via pymoo (minimizacion). `punto_ref` debe dominar (ser >= en cada
    objetivo) a todos los puntos para que el HV sea > 0. Import perezoso: solo se
    necesita pymoo cuando de verdad se calcula HV.
    """
    from pymoo.indicators.hv import HV   # import perezoso (dependencia opcional)

    P = np.asarray(puntos, dtype=float)
    ref = np.asarray(punto_ref, dtype=float)
    return float(HV(ref_point=ref)(P))
