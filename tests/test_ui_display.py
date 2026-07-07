# -*- coding: utf-8 -*-
"""
Test de la funcion PURA de presentacion `ui.steps.paso_resultados.tabla_display`
(aplana la tabla estructurada a "media (desv)"/"N/A" + mascara del mejor).
No arranca streamlit: solo importa el modulo y ejerce la funcion pura.
"""
from __future__ import annotations

import pandas as pd

from domain import tables
from ui.steps import paso_resultados


def _res(moea, valores, mop="DTLZ2", m=2, N=100) -> dict:
    return {"mop": mop, "m": m, "N": N, "moea": moea,
            "indicador": "IGD", "valores": list(valores)}


def test_tabla_display_formato_mascara_y_na():
    # IGD (min): A gana en DTLZ2; en WFG3 solo hay A -> B queda faltante (N/A).
    res = [
        _res("A", [0.010, 0.011, 0.012]),
        _res("B", [0.100, 0.110, 0.120]),
        _res("A", [0.50, 0.51, 0.52], mop="WFG3", m=3),
    ]
    est = tables.tabla_estructurada(res, "IGD", moeas=["A", "B"])
    display, mask = paso_resultados.tabla_display(est, ["A", "B"])

    assert list(display.columns) == ["MOP", "m", "N", "A", "B"]
    assert list(mask.columns) == ["MOP", "m", "N", "A", "B"]

    # Fila DTLZ2: A = mejor (rank 1) -> resaltado; formato "media (desv)" cientifico.
    dtlz2 = display[display["MOP"] == "DTLZ2"].iloc[0]
    assert dtlz2["A"] == "1.100e-02 (1.000e-03)"
    assert dtlz2["B"].startswith("1.100e-01")
    mdtlz2 = mask[display["MOP"] == "DTLZ2"].iloc[0]
    assert bool(mdtlz2["A"]) is True and bool(mdtlz2["B"]) is False

    # Fila WFG3: B sin datos -> "N/A" y nunca resaltada.
    wfg3 = display[display["MOP"] == "WFG3"].iloc[0]
    assert wfg3["B"] == "N/A"
    mwfg3 = mask[display["MOP"] == "WFG3"].iloc[0]
    assert bool(mwfg3["B"]) is False
    # A es el unico presente en WFG3 -> rank 1 -> resaltado.
    assert bool(mwfg3["A"]) is True

    # Las columnas indice nunca se resaltan.
    assert not mask[["MOP", "m", "N"]].to_numpy().any()


def test_tabla_display_vacia():
    # Sin filas -> DataFrames vacios pero con las columnas esperadas.
    est = tables.tabla_estructurada([], "IGD", moeas=["A", "B"])
    display, mask = paso_resultados.tabla_display(est, ["A", "B"])
    assert list(display.columns) == ["MOP", "m", "N", "A", "B"]
    assert len(display) == 0 and len(mask) == 0
    assert isinstance(display, pd.DataFrame)
