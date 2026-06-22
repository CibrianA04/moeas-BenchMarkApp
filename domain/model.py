# -*- coding: utf-8 -*-
"""
Modelo de dominio: estructuras de datos del proyecto.
Sin logica de calculo; solo define las "formas" que viajan entre capas.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# Convenciones de la literatura.
CORRIDAS_ESTANDAR = 30   # corridas independientes por par (MOEA, MOP)
CORRIDAS_MINIMAS = 5     # por debajo de esto, la app advierte


@dataclass
class ConfigCSV:
    """Como interpretar los archivos de PFA al leerlos (capa de datos)."""
    separador: str = ","
    decimal: str = "."
    cabecera_Nm: bool = False     # primera linea '# N m' (N puntos, m objetivos)
    encoding: str = "utf-8"


@dataclass
class PFA:
    """
    Aproximacion al frente de Pareto de UNA corrida.
    Unidad de carga = 1 CSV = 1 PFA: N filas (puntos) x m columnas (objetivos).
    """
    moea: str
    mop: str
    m: int
    corrida: int
    puntos: np.ndarray            # forma (N, m)
    archivo: str = ""


@dataclass
class MapeoArchivo:
    """Una linea por archivo:  archivo = (MOEA, MOP, corrida)."""
    archivo: str
    moea: str
    mop: str
    m: int
    corrida: int


@dataclass
class Proyecto:
    """Contenedor de todo el experimento (se persiste en SQLite a futuro)."""
    nombre: str = "experimento_demo"
    config_csv: ConfigCSV = field(default_factory=ConfigCSV)
    mapeos: list[MapeoArchivo] = field(default_factory=list)
    # FUTURO: frentes de referencia por MOP, indicadores elegidos, resultados...
