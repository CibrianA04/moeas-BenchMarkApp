# -*- coding: utf-8 -*-
"""
Lectura de archivos de PFA y frentes de referencia (STUBS).

Convencion: un CSV = un PFA = N filas (puntos) x m columnas (objetivos).
Opcionalmente la 1a linea es cabecera '# N m'.
"""
from __future__ import annotations


def leer_pfa(origen, config) -> "object":
    """
    STUB. FUTURO: parsea el CSV segun 'config' (separador, decimal, cabecera
    '# N m', encoding) y devuelve una matriz numpy de forma (N, m). 'origen'
    puede ser una ruta o un buffer subido desde la UI.
    """
    raise NotImplementedError("Lectura real de CSV pendiente (capa de datos).")


def inferir_mapeo_desde_nombre(nombre: str):
    """
    STUB. FUTURO: deduce (MOEA, MOP, corrida) a partir de un patron de nombre
    (p. ej. 'nsga2_dtlz2_r01.csv'). Devuelve None mientras no se implemente.
    """
    _ = nombre
    return None
