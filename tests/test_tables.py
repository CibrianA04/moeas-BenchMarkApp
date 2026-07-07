# -*- coding: utf-8 -*-
"""
Tests de statistics.ranking/rango_promedio y de domain/tables.py (tabla
estructurada + renders LaTeX/CSV al estilo de createIndicatorTable.R).
Usa `resultados` sinteticos con la MISMA forma que produce evaluacion.evaluar.
"""
from __future__ import annotations

import io

import pandas as pd
import pytest

from domain import statistics, tables


def _res(indicador, moea, valores, mop="DTLZ2", m=2, N=100) -> dict:
    """Un registro con la MISMA forma que produce evaluacion.evaluar."""
    return {"mop": mop, "m": m, "N": N, "moea": moea,
            "indicador": indicador, "valores": list(valores)}


# Fixture comun: IGD (min) con 3 MOEAs, 2 MOPs y 2 N en DTLZ2.
#  - DTLZ2 N=100: Alg1 gana; vence con significancia a Alg2 (muestras separadas)
#    pero NO a Alg3 (outlier: peor media pero muestras traslapadas).
#  - DTLZ2 N=200: muestras traslapadas -> ranking 1..3 sin significancia.
#  - WFG3  N=100: solo Alg1 y Alg2 (Alg3 faltante -> celda N/A).
def _fixture() -> list[dict]:
    return [
        _res("IGD", "Alg1", [0.010, 0.011, 0.012, 0.013, 0.014]),
        _res("IGD", "Alg2", [0.100, 0.110, 0.120, 0.130, 0.140]),
        _res("IGD", "Alg3", [0.005, 0.006, 0.007, 0.008, 1.000]),
        _res("IGD", "Alg1", [0.20, 0.30, 0.40], N=200),
        _res("IGD", "Alg2", [0.22, 0.28, 0.41], N=200),
        _res("IGD", "Alg3", [0.21, 0.33, 0.39], N=200),
        _res("IGD", "Alg1", [0.50, 0.51, 0.52, 0.53], mop="WFG3", m=3),
        _res("IGD", "Alg2", [0.60, 0.61, 0.62, 0.63], mop="WFG3", m=3),
    ]


# ── ranking ──────────────────────────────────────────────────────────────────
def test_ranking_direccion_por_sentido():
    res = [_res("HV", "A", [1.0]), _res("HV", "B", [2.0]),
           _res("IGD", "A", [1.0]), _res("IGD", "B", [2.0])]
    df = statistics.ranking(res)
    hv = df[df["indicador"] == "HV"].set_index("moea")["rank"]
    igd = df[df["indicador"] == "IGD"].set_index("moea")["rank"]
    assert hv["B"] == 1 and hv["A"] == 2       # 'max': mayor media primero
    assert igd["A"] == 1 and igd["B"] == 2     # 'min': menor media primero


def test_ranking_desempate_por_orden_de_aparicion():
    # Mismas medias (2.0): rank 1 para quien APARECE primero (Zeta), no el
    # alfabetico (Alfa). Replica el order() estable de R.
    res = [_res("HV", "Zeta", [1.0, 3.0]), _res("HV", "Alfa", [2.0, 2.0])]
    ranks = statistics.ranking(res).set_index("moea")["rank"]
    assert ranks["Zeta"] == 1 and ranks["Alfa"] == 2


def test_ranking_rank1_coincide_con_ganador_de_significancia():
    res = _fixture() + [_res("HV", "X", [1.0, 2.0, 3.0, 4.0, 5.0]),
                        _res("HV", "Y", [10.0, 11.0, 12.0, 13.0, 14.0])]
    rnk = statistics.ranking(res)
    sig = statistics.significancia(res)
    assert not sig.empty
    for t in sig.itertuples(index=False):
        fila1 = rnk[(rnk["mop"] == t.mop) & (rnk["m"] == t.m) &
                    (rnk["N"] == t.N) & (rnk["indicador"] == t.indicador) &
                    (rnk["rank"] == 1)]
        assert fila1["moea"].iloc[0] == t.ganador


def test_rango_promedio():
    res = [_res("IGD", "A", [1.0]), _res("IGD", "B", [2.0]),
           _res("IGD", "A", [1.0], N=200), _res("IGD", "B", [2.0], N=200)]
    prom = statistics.rango_promedio(statistics.ranking(res))
    assert list(prom.columns) == ["indicador", "moea", "rank_promedio"]
    por_moea = prom.set_index("moea")["rank_promedio"]
    assert por_moea["A"] == pytest.approx(1.0)
    assert por_moea["B"] == pytest.approx(2.0)


# ── a_latex_doc: golden strings del formato del R ────────────────────────────
def test_latex_golden_colores_marcas_y_na():
    est = tables.tabla_estructurada(_fixture(), "IGD")
    tex = tables.a_latex_doc(est, "IGD", "Tabla IGD", "tab:igd")
    # rank 1: gris 0.5, %.3e, sin '\#'
    assert r"\cellcolor[gray]{0.5} \specialcell{1.200e-02$^{1}$ \\ (1.581e-03)}" in tex
    # rank 2 significativo: gris 0.8 + '\#'
    assert r"\cellcolor[gray]{0.8} \specialcell{1.200e-01$^{2}$\# \\ (1.581e-02)}" in tex
    # rank 2 NO significativo (DTLZ2 N=200): sin '\#'
    assert r"$^{2}$ \\" in tex
    # ni el ganador ni los rank 3 (aqui no significativos) llevan '\#'
    assert r"$^{1}$\#" not in tex
    assert r"$^{3}$\#" not in tex
    # celda sin datos (WFG3 x Alg3)
    assert "& N/A" in tex
    assert r"\caption{Tabla IGD}" in tex
    assert r"\label{tab:igd}" in tex


def test_latex_estructura_columnas_multirow_hline():
    est = tables.tabla_estructurada(_fixture(), "IGD")
    tex = tables.a_latex_doc(est, "IGD", "c", "l")
    # 3 columnas indice + 3 MOEAs
    assert r"\begin{tabular}{|c|c|c|c|c|c|}" in tex
    assert (r"{\bf MOP} & {\bf m} & {\bf N} & {\bf Alg1} & {\bf Alg2}"
            r" & {\bf Alg3} \\") in tex
    # \multirow por MOP (y su m); k = numero de filas (N) del MOP
    assert r"\multirow{2}{*}{DTLZ2} & \multirow{2}{*}{2} & 100" in tex
    assert r"\multirow{1}{*}{WFG3} & \multirow{1}{*}{3} & 100" in tex
    assert "\n& & 200" in tex                  # 2a fila del bloque DTLZ2
    assert r"\cline{3-6}" in tex               # no corta las columnas multirow
    assert "\\hline\n\\hline" in tex           # separador entre MOPs


def test_latex_escapa_guiones_bajos_en_moeas():
    res = [_res("IGD", "Two_Arch2", [0.1, 0.2]), _res("IGD", "NSGAII", [0.3, 0.4])]
    est = tables.tabla_estructurada(res, "IGD")
    tex = tables.a_latex_doc(est, "IGD", "c", "l")
    assert r"{\bf Two\_Arch2}" in tex


def test_moeas_explicitos_definen_columnas_orden_y_na():
    # Universo fijo estilo R: un MOEA sin datos produce columna de N/A.
    est = tables.tabla_estructurada(_fixture(), "IGD",
                                    moeas=["Alg2", "Alg1", "Fantasma"])
    tex = tables.a_latex_doc(est, "IGD", "c", "l")
    assert r"& {\bf Alg2} & {\bf Alg1} & {\bf Fantasma} \\" in tex
    assert "& N/A" in tex


# ── filtro_n: la vista completa vs la publicable ─────────────────────────────
def test_filtro_n_none_int_y_dict():
    res = _fixture()
    todas = tables.tabla_estructurada(res, "IGD")
    assert len(todas) == 3                     # (DTLZ2,100) (DTLZ2,200) (WFG3,100)

    solo_100 = tables.tabla_estructurada(res, "IGD", filtro_n=100)
    assert len(solo_100) == 2
    assert set(solo_100[("N", "")]) == {100}

    canon = tables.tabla_estructurada(res, "IGD", filtro_n={"DTLZ2": 200})
    assert len(canon) == 1                     # WFG3 no listado -> se omite
    assert canon[("MOP", "")].iloc[0] == "DTLZ2"
    assert canon[("N", "")].iloc[0] == 200


# ── a_csv_doc ────────────────────────────────────────────────────────────────
def test_csv_largo_filas_y_columnas():
    est = tables.tabla_estructurada(_fixture(), "IGD")
    df = pd.read_csv(io.BytesIO(tables.a_csv_doc(est)))
    assert list(df.columns) == ["MOP", "m", "N", "MOEA",
                                "media", "desv", "rank", "sig"]
    assert len(df) == 3 * 3                    # filas x MOEAs (incluye faltantes)
    falta = df[(df["MOP"] == "WFG3") & (df["MOEA"] == "Alg3")].iloc[0]
    assert pd.isna(falta["media"]) and pd.isna(falta["rank"])
    gana = df[(df["MOP"] == "DTLZ2") & (df["N"] == 100) & (df["MOEA"] == "Alg1")].iloc[0]
    assert gana["rank"] == 1 and str(gana["sig"]) == "False"
    marcado = df[(df["MOP"] == "DTLZ2") & (df["N"] == 100) & (df["MOEA"] == "Alg2")].iloc[0]
    assert marcado["rank"] == 2 and str(marcado["sig"]) == "True"
