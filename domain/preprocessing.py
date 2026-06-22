# -*- coding: utf-8 -*-
"""
Preprocesamiento de cada PFA antes de evaluar indicadores (STUBS).
Todo aqui es puro (numpy); sin Streamlit.
"""
from __future__ import annotations

import numpy as np


def filtrar_no_dominadas(puntos: np.ndarray) -> np.ndarray:
    """STUB: conservar solo el conjunto no dominado. FUTURO: filtrado real."""
    return puntos


def eliminar_duplicados(puntos: np.ndarray) -> np.ndarray:
    """Quita filas repetidas (esto si es trivial y seguro)."""
    return np.unique(puntos, axis=0)


def estimar_ideal_nadir(conjunto: np.ndarray):
    """
    STUB: estima (ideal, nadir) a partir de un conjunto de puntos.
    FUTURO: manejo de DRS (soluciones resistentes a la dominancia) para que el
    nadir no se contamine.
    """
    ideal = conjunto.min(axis=0)
    nadir = conjunto.max(axis=0)
    return ideal, nadir


def normalizar(puntos: np.ndarray, ideal: np.ndarray, nadir: np.ndarray) -> np.ndarray:
    """STUB: normaliza a [0,1] con ideal/nadir. FUTURO: variantes/no lineales."""
    rango = np.where(nadir > ideal, nadir - ideal, 1.0)
    return (puntos - ideal) / rango
