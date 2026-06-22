# -*- coding: utf-8 -*-
"""
Construccion y exportacion de TABLAS de resultados.

Regla: UNA tabla por indicador (no mezclar indicadores: escalas y direcciones
distintas, y los tests corren por indicador). Celda = media (desv) sobre corridas.
Devuelve DataFrames y cadenas; no importa Streamlit.
"""
from __future__ import annotations

import pandas as pd

from . import mock


def tabla_medias_desv(ind_id: str, moeas: list[str], mops: list[tuple[str, int]]):
    """
    (STUB con datos de ejemplo) Devuelve (medias, desv) para UN indicador:
        filas = MultiIndex (MOP, m) · columnas = MOEAs.
    FUTURO: agregar las corridas reales por (MOEA, MOP) con statistics.agregar.
    """
    return mock.tabla_medias_desv(ind_id, moeas, mops)


def texto_celdas(medias: pd.DataFrame, desv: pd.DataFrame,
                 formato: str = "media (desv)") -> pd.DataFrame:
    """Combina medias y desviaciones en texto para mostrar."""
    out = medias.copy()
    for col in out.columns:
        if formato == "media +/- desv":
            out[col] = [f"{m:.3e} +/- {s:.1e}" for m, s in zip(medias[col], desv[col])]
        elif formato == "solo media":
            out[col] = [f"{m:.3e}" for m in medias[col]]
        else:  # "media (desv)"
            out[col] = [f"{m:.3e} ({s:.1e})" for m, s in zip(medias[col], desv[col])]
    return out


def mascara_mejor(medias: pd.DataFrame, sentido: str) -> pd.DataFrame:
    """DataFrame booleano marcando la mejor media por fila (segun 'sentido')."""
    if sentido == "max":
        return medias.eq(medias.max(axis=1), axis=0)
    return medias.eq(medias.min(axis=1), axis=0)


def a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def a_latex(df: pd.DataFrame, caption: str, label: str) -> str:
    return df.to_latex(index=False, escape=True, caption=caption, label=label)
