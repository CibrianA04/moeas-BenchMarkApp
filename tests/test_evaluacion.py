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
from domain import evaluacion
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
