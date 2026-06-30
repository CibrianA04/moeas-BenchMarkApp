# -*- coding: utf-8 -*-
"""
Preprocesamiento de cada PFA antes de evaluar indicadores.
Todo aqui es puro (numpy); sin Streamlit.

Convencion: se asume MINIMIZACION en el espacio de objetivos (menor es mejor),
que es la convencion de los .pof de este proyecto y la que espera pymoo para HV.
"""
from __future__ import annotations

import numpy as np


def filtrar_no_dominadas(puntos: np.ndarray) -> np.ndarray:
    """
    Conserva solo el conjunto NO DOMINADO (Pareto, minimizacion).

    Un punto j domina a i si j es <= i en TODOS los objetivos y < i en ALGUNO.
    Se eliminan los i dominados por algun j; los duplicados exactos NO se dominan
    entre si (sobreviven; usar eliminar_duplicados aparte si se desea).
    O(n^2 * m); suficiente para los tamanos de PFA/frentes de este proyecto.
    """
    P = np.asarray(puntos, dtype=float)
    n = P.shape[0]
    if n <= 1:
        return P.copy()

    es_no_dom = np.ones(n, dtype=bool)
    for i in range(n):
        mejor_o_igual = np.all(P <= P[i], axis=1)   # j no es peor que i en nada
        estricto = np.any(P < P[i], axis=1)         # j es mejor que i en algo
        domina_a_i = mejor_o_igual & estricto       # j domina a i (incluye j=i? no:
        domina_a_i[i] = False                       #   i nunca se domina a si mismo)
        if domina_a_i.any():
            es_no_dom[i] = False
    return P[es_no_dom]


def eliminar_duplicados(puntos: np.ndarray) -> np.ndarray:
    """Quita filas repetidas (trivial y seguro)."""
    P = np.asarray(puntos, dtype=float)
    if P.shape[0] == 0:
        return P.copy()
    return np.unique(P, axis=0)


def estimar_ideal_nadir(conjunto: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Estima (ideal, nadir) por objetivo a partir de un conjunto de puntos:
    ideal = minimo por columna, nadir = maximo por columna (minimizacion).

    FUTURO: manejo de DRS (soluciones resistentes a la dominancia) para que el
    nadir no se contamine; por ahora es el maximo crudo del conjunto.
    """
    C = np.asarray(conjunto, dtype=float)
    if C.shape[0] == 0:
        raise ValueError("No se puede estimar ideal/nadir de un conjunto vacio.")
    return C.min(axis=0), C.max(axis=0)


def normalizar(puntos: np.ndarray, ideal: np.ndarray, nadir: np.ndarray) -> np.ndarray:
    """
    Normaliza a [0,1] con (ideal, nadir): (p - ideal) / (nadir - ideal).
    Si algun objetivo tiene rango nulo (nadir == ideal), usa 1.0 para no dividir
    entre cero (esa columna queda en 0).
    """
    P = np.asarray(puntos, dtype=float)
    ideal = np.asarray(ideal, dtype=float)
    nadir = np.asarray(nadir, dtype=float)
    rango = np.where(nadir > ideal, nadir - ideal, 1.0)
    return (P - ideal) / rango
