# -*- coding: utf-8 -*-
"""
Tests de domain/statistics.py: resumen (media/desv), corrida mediana y el PREVIEW
de significancia (Mann-Whitney U de una cola hacia el ganador segun el sentido).
"""
from __future__ import annotations

import pytest

from domain import statistics


def _res(indicador, moea, valores, mop="DTLZ2", m=2, N=100) -> dict:
    """Un registro con la MISMA forma que produce evaluacion.evaluar."""
    return {"mop": mop, "m": m, "N": N, "moea": moea,
            "indicador": indicador, "valores": list(valores)}


# ── resumen ──────────────────────────────────────────────────────────────────
def test_resumen_media_y_desv_a_mano():
    df = statistics.resumen([_res("HV", "A", [1.0, 2.0, 3.0])])
    fila = df.iloc[0]
    assert fila["media"] == pytest.approx(2.0)
    assert fila["desv"] == pytest.approx(1.0)      # std muestral (ddof=1) de [1,2,3]
    assert fila["n"] == 3
    assert (fila["mop"], fila["m"], fila["N"], fila["indicador"], fila["moea"]) == \
        ("DTLZ2", 2, 100, "HV", "A")


# ── corrida mediana (mediana POR indicador; n par -> inferior) ───────────────
def test_indice_mediana_impar():
    # [3,1,2]: la mediana es de valor 2, que esta en el indice 2 del original.
    idx = statistics.indice_mediana([3.0, 1.0, 2.0])
    assert idx == 2
    assert [3.0, 1.0, 2.0][idx] == 2.0


def test_indice_mediana_par_usa_inferior():
    # [4,1,3,2]: ordenado [1,2,3,4], mediana INFERIOR = 2, en el indice 3.
    idx = statistics.indice_mediana([4.0, 1.0, 3.0, 2.0])
    assert idx == 3
    assert [4.0, 1.0, 3.0, 2.0][idx] == 2.0


def test_corrida_mediana_dataframe():
    df = statistics.corrida_mediana([_res("IGD", "A", [3.0, 1.0, 2.0])])
    fila = df.iloc[0]
    assert fila["indice"] == 2
    assert fila["valor"] == pytest.approx(2.0)


# ── significancia (PREVIEW) ──────────────────────────────────────────────────
_A = [1.0, 2.0, 3.0, 4.0, 5.0]           # media 3
_B = [10.0, 11.0, 12.0, 13.0, 14.0]      # media 12 (grupos bien separados)


def test_significancia_min_menor_media_gana_y_es_significativo():
    df = statistics.significancia([_res("IGD", "A", _A), _res("IGD", "B", _B)])
    assert len(df) == 1
    fila = df.iloc[0]
    assert fila["ganador"] == "A"                 # 'min': gana la MENOR media
    assert fila["rival"] == "B"
    assert fila["alternativa"] == "less"
    assert fila["p_value"] <= 0.05
    assert bool(fila["significativo"]) is True


def test_significancia_sentido_max_invierte_ganador():
    # MISMOS datos, pero indicador 'max' (HV): ahora gana la MAYOR media.
    df = statistics.significancia([_res("HV", "A", _A), _res("HV", "B", _B)])
    fila = df.iloc[0]
    assert fila["ganador"] == "B"                  # invertido respecto al caso 'min'
    assert fila["alternativa"] == "greater"
    assert fila["p_value"] <= 0.05
    assert bool(fila["significativo"]) is True
