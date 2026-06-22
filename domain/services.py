# -*- coding: utf-8 -*-
"""
Facade del dominio para operaciones respaldadas por la capa de DATOS.

Existe para mantener la dependencia en un solo sentido: la UI llama a estos
servicios (dominio) y el dominio llama a 'data'. Asi la UI nunca importa 'data'.
"""
from __future__ import annotations

import pandas as pd

from data import csv_io, persistence
from . import mock
from .model import ConfigCSV, Proyecto


def preview_pfa(origen=None, config: ConfigCSV | None = None) -> pd.DataFrame:
    """
    Devuelve una vista previa de un PFA.
    MAQUETA: regresa datos de ejemplo.
    FUTURO: return csv_io.leer_pfa(origen, config) -> matriz N x m envuelta en DataFrame.
    """
    _ = (origen, config)         # se usaran a futuro
    return mock.preview_df()


def inferir_mapeo(nombres: list[str]):
    """
    FUTURO: deduce (MOEA, MOP, corrida) desde cada nombre de archivo usando
    csv_io.inferir_mapeo_desde_nombre. En la maqueta la UI usa filas de ejemplo.
    """
    return [csv_io.inferir_mapeo_desde_nombre(n) for n in nombres]


def guardar_proyecto(proy: Proyecto) -> str:
    """MAQUETA: no persiste todavia. FUTURO: persistence.guardar(proy) en SQLite."""
    _ = proy
    return "FUTURO: guardar el proyecto en SQLite (aun no implementado)."


def cargar_proyecto(ruta: str = "proyecto.sqlite") -> str:
    """MAQUETA: no carga todavia. FUTURO: persistence.cargar(ruta)."""
    _ = ruta
    return "FUTURO: cargar el proyecto desde SQLite (aun no implementado)."
