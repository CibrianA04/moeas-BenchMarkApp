# -*- coding: utf-8 -*-
"""
Facade del dominio para operaciones respaldadas por la capa de DATOS.

Existe para mantener la dependencia en un solo sentido: la UI llama a estos
servicios (dominio) y el dominio llama a 'data'. Asi la UI nunca importa 'data'.
La UI lee los bytes de los archivos subidos y se los pasa a estas funciones.
"""
from __future__ import annotations

import io

import pandas as pd

from data import csv_io
from .model import PFA, ConfigCSV, Proyecto

# Columnas del mapeo (una linea por archivo).
COLS_MAPEO = ["archivo", "MOEA", "MOP", "m", "n", "corrida"]


# ─────────────────────────────────────────────────────────────────────────────
#  Ingesta de datos reales (.zip = flujo principal; .pof sueltos = pruebas)
# ─────────────────────────────────────────────────────────────────────────────
def cargar_zip(zip_bytes, config: ConfigCSV | None = None
               ) -> tuple[list[PFA], list[tuple[str, str]]]:
    """
    Procesa el .zip subido por el usuario (en memoria) y devuelve (pfas, errores),
    donde errores = [(archivo, motivo), ...] de los .pof que se omitieron.
    """
    errores: list[tuple[str, str]] = []
    pfas = list(csv_io.iterar_pofs_zip(zip_bytes, config=config, errores=errores))
    return pfas, errores


def cargar_pofs(archivos, config: ConfigCSV | None = None
                ) -> tuple[list[PFA], list[tuple[str, str]]]:
    """
    Procesa .pof SUELTOS (para pruebas rapidas). 'archivos' = [(nombre, bytes), ...].
    Devuelve (pfas, errores) igual que cargar_zip; no aborta el lote por uno malo.
    """
    errores: list[tuple[str, str]] = []
    pfas: list[PFA] = []
    for nombre, datos in archivos:
        try:
            pfas.append(csv_io.leer_pfa_buffer(io.BytesIO(datos), nombre, config))
        except Exception as exc:  # noqa: BLE001
            errores.append((nombre, str(exc)))
    return pfas, errores


# ─────────────────────────────────────────────────────────────────────────────
#  Vistas que consume la UI (sin que la UI importe 'data')
# ─────────────────────────────────────────────────────────────────────────────
def mapeo_desde_pfas(pfas: list[PFA]) -> pd.DataFrame:
    """Tabla de mapeo autocompletada desde el nombre de cada PFA."""
    filas = [
        {"archivo": p.archivo, "MOEA": p.moea, "MOP": p.mop,
         "m": p.m, "n": p.n, "corrida": p.corrida}
        for p in pfas
    ]
    return pd.DataFrame(filas, columns=COLS_MAPEO)


def preview_de_pfa(pfa: PFA, n: int = 8) -> pd.DataFrame:
    """Primeras 'n' filas (puntos REALES) del PFA, con columnas f1..fm."""
    columnas = [f"f{j + 1}" for j in range(pfa.m)]
    return pd.DataFrame(pfa.puntos[:n], columns=columnas)


# ─────────────────────────────────────────────────────────────────────────────
#  Persistencia del proyecto (aun stub; lo usa la barra lateral)
# ─────────────────────────────────────────────────────────────────────────────
def guardar_proyecto(proy: Proyecto) -> str:
    """MAQUETA: no persiste todavia. FUTURO: persistence.guardar(proy) en SQLite."""
    _ = proy
    return "FUTURO: guardar el proyecto en SQLite (aun no implementado)."


def cargar_proyecto(ruta: str = "proyecto.sqlite") -> str:
    """MAQUETA: no carga todavia. FUTURO: persistence.cargar(ruta)."""
    _ = ruta
    return "FUTURO: cargar el proyecto desde SQLite (aun no implementado)."
