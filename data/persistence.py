# -*- coding: utf-8 -*-
"""
Persistencia del proyecto en SQLite (STUBS).

FUTURO (esquema tentativo):
    proyecto(id, nombre, config_csv_json)
    mapeo(id, proyecto_id, archivo, moea, mop, m, corrida)
    referencia(id, proyecto_id, mop, m, archivo)
    resultado(id, proyecto_id, indicador, moea, mop, corrida, valor)
"""
from __future__ import annotations

import sqlite3  # stdlib; se usara a futuro  # noqa: F401


def guardar(proyecto, ruta: str = "proyecto.sqlite") -> None:
    """STUB. FUTURO: vuelca el proyecto completo a una base SQLite."""
    raise NotImplementedError("Persistencia SQLite pendiente.")


def cargar(ruta: str = "proyecto.sqlite"):
    """STUB. FUTURO: reconstruye el proyecto desde SQLite."""
    raise NotImplementedError("Carga SQLite pendiente.")
