# -*- coding: utf-8 -*-
"""
Tests de statistics.critical_differences (Nemenyi / Demsar 2006 sobre los
rangos promedio que ya calcula rango_promedio) y de
figures.figura_critical_differences. HEADLESS: sin streamlit ni archivos.
"""
from __future__ import annotations

import math

import pytest
from matplotlib.figure import Figure

from domain import figures, statistics


def _res(moea, valor, mop="DTLZ2", m=2, N=100, indicador="IGD") -> dict:
    """Un registro con la MISMA forma que produce evaluacion.evaluar."""
    return {"mop": mop, "m": m, "N": N, "moea": moea,
            "indicador": indicador, "valores": [valor]}


def _tres_moeas_diez_escenarios() -> list[dict]:
    # IGD (min): A < B < C en TODOS los escenarios -> rangos fijos 1, 2, 3.
    return [_res(mo, v, mop=f"MOP{i}")
            for i in range(10) for mo, v in (("A", 0.1), ("B", 0.2), ("C", 0.3))]


def test_cd_valor_conocido_k3_n10():
    cd = statistics.critical_differences(_tres_moeas_diez_escenarios())["IGD"]
    assert cd.k == 3 and cd.N == 10
    # q_{0.05, 3, inf} / sqrt(2) = 2.3437 (tabla de Demsar 2006).
    assert cd.cd == pytest.approx(2.3437 * math.sqrt(3 * 4 / (6 * 10)), rel=1e-3)
    assert cd.rank_promedio == {"A": 1.0, "B": 2.0, "C": 3.0}
    # CD ~ 1.048: A-B y B-C se unen (dif. 1); A-C no (dif. 2 > CD).
    assert cd.grupos == [("A", "B"), ("B", "C")]


def test_cd_k2_coherente_con_z_normal():
    # Con k=2, q_{0.05, 2, inf} / sqrt(2) = z_{0.975} = 1.95996.
    res = [_res(mo, v, mop=f"MOP{i}")
           for i in range(4) for mo, v in (("A", 0.1), ("B", 0.2))]
    cd = statistics.critical_differences(res)["IGD"]
    assert cd.k == 2 and cd.N == 4
    assert cd.cd == pytest.approx(1.95996 * math.sqrt(2 * 3 / (6 * 4)), rel=1e-4)
    # Diferencia de rangos = 1 > CD (~0.98): ningun grupo se une.
    assert cd.grupos == []


def test_cd_k2_con_pocos_escenarios_une_el_grupo():
    res = [_res(mo, v, mop=f"MOP{i}")
           for i in range(2) for mo, v in (("A", 0.1), ("B", 0.2))]
    cd = statistics.critical_differences(res)["IGD"]
    # CD = 1.95996 * sqrt(6/12) ~ 1.386 > 1: A y B no difieren -> una barra.
    assert cd.cd > 1.0
    assert cd.grupos == [("A", "B")]


def test_cd_omite_indicador_con_un_solo_moea():
    res = [_res("A", 0.1, mop=f"MOP{i}") for i in range(5)]
    assert statistics.critical_differences(res) == {}


def test_figura_cd_devuelve_figure_sin_lanzar():
    cd = statistics.critical_differences(_tres_moeas_diez_escenarios())["IGD"]
    fig = figures.figura_critical_differences(cd, titulo="t")
    try:
        assert isinstance(fig, Figure)
        assert fig.axes                      # el eje (apagado) del diagrama
    finally:
        figures.cerrar(fig)
