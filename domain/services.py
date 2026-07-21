# -*- coding: utf-8 -*-
"""
Fachada del dominio para operaciones respaldadas por la capa de DATOS.

Existe para mantener la dependencia en un solo sentido: la UI llama a estos
servicios (dominio) y el dominio llama a 'data'. Asi la UI nunca importa 'data'.
La UI lee los bytes de los archivos subidos y se los pasa a estas funciones.
"""
from __future__ import annotations

import io

import pandas as pd

from data import csv_io, persistence
from .model import PFA, ConfigCSV

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


def cargar_frentes_referencia_zip(zip_bytes, config: ConfigCSV | None = None
                                  ) -> tuple[dict[tuple[str, int], object], list[tuple[str, str]]]:
    """Procesa un .zip de frentes de referencia subido por el usuario."""
    return csv_io.leer_frentes_de_zip(zip_bytes, config=config)


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


def cobertura_frentes_referencia(pares, dir_ref=None, mapeo: dict | None = None,
                                 override: dict[tuple[str, int], object] | None = None) -> pd.DataFrame:
    """Devuelve la cobertura de frentes de referencia como DataFrame."""
    filas = csv_io.cobertura_frentes_referencia(pares, dir_ref=dir_ref,
                                                mapeo=mapeo, override=override)
    return pd.DataFrame(filas)


# ─────────────────────────────────────────────────────────────────────────────
#  Persistencia del proyecto: snapshot SQLite de SESION (lo usa la barra
#  lateral). La UI arma el `estado` desde session_state y NUNCA toca data/
#  ni sqlite3 directo. El snapshot no guarda parametros de calculo (punto de
#  referencia de HV, p de Dp...): eso es reproducibilidad, trabajo futuro.
#
#  Contrato del dict `estado` (todas las claves opcionales):
#    nombre, paso, completado, separador, decimal, indicadores  -> meta
#    pfas: list[PFA]                       (dataclasses de domain.model)
#    frentes_ref: dict[(mop, m)] -> ndarray
#    resultados / omitidos: list[dict]     (salida de evaluacion.evaluar)
# ─────────────────────────────────────────────────────────────────────────────
def _snapshot_plano(estado: dict) -> dict:
    """PFA -> dict y frentes dict -> filas: lo que espera data/persistence."""
    plano = dict(estado)
    plano["pfas"] = [
        {"moea": p.moea, "mop": p.mop, "m": p.m, "n": p.n,
         "corrida": p.corrida, "archivo": p.archivo, "puntos": p.puntos}
        for p in (estado.get("pfas") or [])]
    plano["frentes_ref"] = [
        {"mop": mop, "m": m, "puntos": puntos}
        for (mop, m), puntos in (estado.get("frentes_ref") or {}).items()]
    return plano


def _reconstruir_estado(plano: dict) -> dict:
    """Inverso de _snapshot_plano: dicts -> dataclasses PFA y dict de frentes."""
    estado = dict(plano)
    estado["pfas"] = [
        PFA(moea=d["moea"], mop=d["mop"], m=int(d["m"]), n=int(d["n"]),
            corrida=int(d["corrida"]), puntos=d["puntos"],
            archivo=d.get("archivo", ""))
        for d in (plano.get("pfas") or [])]
    estado["frentes_ref"] = {(f["mop"], int(f["m"])): f["puntos"]
                             for f in (plano.get("frentes_ref") or [])}
    return estado


def guardar_proyecto(estado: dict, ruta) -> None:
    """Guarda el snapshot de sesion `estado` en el archivo .sqlite `ruta`."""
    persistence.guardar(_snapshot_plano(estado), ruta)


def proyecto_a_bytes(estado: dict) -> bytes:
    """Snapshot como bytes .sqlite, para ofrecerlo como descarga en la UI
    (el disco de Streamlit Cloud es efimero: no sirve una ruta fija)."""
    return persistence.a_bytes(_snapshot_plano(estado))


def cargar_proyecto(fuente) -> dict:
    """
    Carga un snapshot desde una ruta .sqlite o desde BYTES subidos, con los PFA
    como dataclasses y los frentes como {(mop, m): puntos}. Los errores salen
    como FileNotFoundError/ValueError con mensaje claro (la UI los muestra).
    """
    if isinstance(fuente, (bytes, bytearray)):
        plano = persistence.desde_bytes(fuente)
    else:
        plano = persistence.cargar(fuente)
    return _reconstruir_estado(plano)
