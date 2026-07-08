# -*- coding: utf-8 -*-
"""
Tests de domain/evaluacion.py: agrupacion por escenario (MOP, m, N), valores por
corrida, escenario sin frente de referencia y prioridad de override.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from data import csv_io
from domain import evaluacion, indicators
from domain.model import PFA

RAIZ = Path(__file__).resolve().parents[1]
EJEMPLOS = RAIZ / "data_ejemplo"


# ── Utilidades para armar PFA de prueba ──────────────────────────────────────
def _pfas_dtlz2(moeas=("NSGAII", "MOEAD"), corridas=(1, 2, 3)) -> list[PFA]:
    """Varios PFA de >=2 MOEAs en un MISMO escenario (DTLZ2, m=2, N=11).

    Reutiliza puntos reales de data_ejemplo (con una perturbacion minima por
    corrida) y reasigna metadatos para que caigan todos en un solo escenario.
    DTLZ2/02D tiene frente de referencia automatico (DTLZ2_02D.pof).
    """
    base = csv_io.leer_pfa(EJEMPLOS / "NSGAII_DTLZ2_02D_N11_R23.pof").puntos
    pfas = []
    for moea in moeas:
        for r in corridas:
            pfas.append(PFA(
                moea=moea, mop="DTLZ2", m=2, n=11, corrida=r,
                puntos=base + 0.001 * r,
                archivo=f"{moea}_DTLZ2_02D_N11_R{r:02d}.pof",
            ))
    return pfas


def _pfas_sin_referencia(corridas=(1, 2)) -> list[PFA]:
    """PFA de un (MOP, m) SIN frente de referencia automatico -> 'NOEXISTE'."""
    rng = np.random.default_rng(0)
    return [
        PFA(moea="A", mop="NOEXISTE", m=2, n=8, corrida=r,
            puntos=rng.random((8, 2)),   # positivos: HV con nadir*1.1 queda finito > 0
            archivo=f"A_NOEXISTE_02D_N8_R{r:02d}.pof")
        for r in corridas
    ]


# ── Agrupacion + valores por corrida ─────────────────────────────────────────
def test_evaluar_agrupa_por_escenario_y_cuenta_corridas():
    resultados, omitidos = evaluacion.evaluar(_pfas_dtlz2(), ["HV", "IGD"])

    assert omitidos == []
    # 2 MOEAs x 2 indicadores = 4 filas, todas en el mismo escenario.
    assert len(resultados) == 4
    for fila in resultados:
        assert (fila["mop"], fila["m"], fila["N"]) == ("DTLZ2", 2, 11)
        assert len(fila["valores"]) == 3                 # una por corrida
        assert all(np.isfinite(v) for v in fila["valores"])

    claves = {(f["moea"], f["indicador"]) for f in resultados}
    assert claves == {("NSGAII", "HV"), ("NSGAII", "IGD"),
                      ("MOEAD", "HV"), ("MOEAD", "IGD")}


def test_evaluar_hv_usa_un_punto_por_escenario():
    # El punto de HV es UNO por escenario: dos MOEAs con los MISMOS puntos por
    # corrida deben dar EXACTAMENTE los mismos valores de HV.
    base = csv_io.leer_pfa(EJEMPLOS / "NSGAII_DTLZ2_02D_N11_R23.pof").puntos
    pfas = [
        PFA(moea=moea, mop="DTLZ2", m=2, n=11, corrida=1, puntos=base.copy(),
            archivo=f"{moea}.pof")
        for moea in ("NSGAII", "MOEAD")
    ]
    resultados, _ = evaluacion.evaluar(pfas, ["HV"])
    hv = {f["moea"]: f["valores"][0] for f in resultados}
    assert hv["NSGAII"] == pytest.approx(hv["MOEAD"])


# ── Escenario sin frente de referencia ───────────────────────────────────────
def test_evaluar_sin_referencia_omite_distancia_pero_calcula_hv():
    resultados, omitidos = evaluacion.evaluar(_pfas_sin_referencia(), ["HV", "IGD"])

    # IGD (requiere_ref) se omite; HV (no requiere ref) si se calcula.
    assert {f["indicador"] for f in resultados} == {"HV"}
    hv = next(f for f in resultados if f["indicador"] == "HV")
    assert len(hv["valores"]) == 2
    assert all(np.isfinite(v) for v in hv["valores"])

    sin_ref = [o for o in omitidos if o["tipo"] == "sin_referencia"]
    assert len(sin_ref) == 1
    assert (sin_ref[0]["mop"], sin_ref[0]["m"], sin_ref[0]["N"]) == ("NOEXISTE", 2, 8)
    assert "IGD" in sin_ref[0]["indicadores_omitidos"]


# ── Punto de referencia de HV (_punto_hv) ────────────────────────────────────
def _grupo(puntos_por_corrida, mop="X") -> list[PFA]:
    """Un escenario sintetico: una lista de PFA (una matriz de puntos por corrida)."""
    return [
        PFA(moea="A", mop=mop, m=p.shape[1], n=p.shape[0], corrida=i,
            puntos=np.asarray(p, dtype=float),
            archivo=f"A_{mop}_{p.shape[1]:02d}D_N{p.shape[0]}_R{i:02d}.pof")
        for i, p in enumerate(puntos_por_corrida, start=1)
    ]


def test_punto_hv_con_objetivos_negativos_domina_al_nadir_y_hv_positivo():
    # Regresion (imita VNT2/VNT3): objetivos en [-5, -1]. Con nadir*1.1 literal el
    # punto quedaba DOMINADO y HV = 0; con margen sobre el rango queda > nadir.
    c1 = np.array([[-5.0, -1.0], [-3.0, -3.0], [-1.0, -5.0]])
    c2 = c1 + 0.5                                    # segunda corrida (union)
    grupo = _grupo([c1, c2])
    punto = evaluacion._punto_hv(grupo, "nadir_x1.1", None, 2)
    nadir = np.vstack([c1, c2]).max(axis=0)
    assert np.all(punto > nadir)                     # domina en CADA componente
    hv = indicators.calcular("HV", c1, punto_ref=punto)
    assert np.isfinite(hv) and hv > 0.0


def test_evaluar_hv_con_objetivos_negativos_es_positivo():
    # End-to-end del bug: evaluar() con el modo default sobre un frente negativo
    # (MOP sin frente de referencia: HV no lo necesita) debe dar HV > 0.
    puntos = np.array([[-5.0, -1.0], [-3.0, -3.0], [-1.0, -5.0]])
    resultados, _ = evaluacion.evaluar(_grupo([puntos], mop="NEGATIVO"), ["HV"])
    assert len(resultados) == 1
    assert all(np.isfinite(v) and v > 0.0 for v in resultados[0]["valores"])


def test_punto_hv_equivale_a_nadir_x1_1_solo_si_ideal_es_cero():
    # Con ideal == 0 en TODAS las columnas: nadir + 0.1*(nadir - 0) == nadir*1.1.
    con_origen = np.array([[0.0, 4.0], [2.0, 0.0]])
    punto = evaluacion._punto_hv(_grupo([con_origen]), "nadir_x1.1", None, 2)
    assert punto == pytest.approx(con_origen.max(axis=0) * 1.1)

    # Con ideal != 0 NO se afirma igualdad con nadir*1.1: solo que supera al nadir.
    desplazado = np.array([[1.0, 3.0], [2.0, 2.0]])
    punto = evaluacion._punto_hv(_grupo([desplazado]), "nadir_x1.1", None, 2)
    assert np.all(punto > desplazado.max(axis=0))


def test_punto_hv_modos_nadir_y_fijo_intactos():
    puntos = np.array([[-5.0, 1.0], [-3.0, 3.0]])
    grupo = _grupo([puntos])
    crudo = evaluacion._punto_hv(grupo, "nadir", None, 2)
    assert crudo == pytest.approx(puntos.max(axis=0))          # max crudo, sin margen
    fijo = evaluacion._punto_hv(grupo, "fijo", [7.0, 8.0], 2)
    assert fijo == pytest.approx([7.0, 8.0])                   # el vector dado tal cual


# ── Prioridad del override (frente subido por el usuario) ─────────────────────
def test_evaluar_override_cambia_el_frente_usado():
    def igd_por_moea(res):
        return {f["moea"]: f["valores"] for f in res if f["indicador"] == "IGD"}

    auto, _ = evaluacion.evaluar(_pfas_dtlz2(), ["IGD"])                # frente automatico
    frente_usuario = np.array([[10.0, 10.0], [20.0, 20.0]])            # frente distinto
    over, omit = evaluacion.evaluar(_pfas_dtlz2(), ["IGD"],
                                    override={("DTLZ2", 2): frente_usuario})

    assert omit == []
    a, o = igd_por_moea(auto), igd_por_moea(over)
    assert set(a) == set(o)                                            # mismos grupos
    for moea in a:
        # Otro frente -> otros valores de IGD (se uso el del usuario).
        assert not np.allclose(a[moea], o[moea])
