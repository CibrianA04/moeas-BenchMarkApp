# -*- coding: utf-8 -*-
"""
Lectura de archivos .pof (PFA) desde disco y desde un .zip subido por el usuario.


Formato .pof
  - Linea 1 = cabecera '# N m' (N puntos, m objetivos). Puede faltar -> por eso se
    salta con comment='#' (no con skiprows), aparezca o no.
  - Resto: un punto por linea, m columnas separadas por ESPACIOS, con un espacio
    final sobrante. Decimal con punto, notacion cientifica, valores posiblemente
    NEGATIVOS. Lectura: sep=r"\\s+" (NO delimiter=" ", que mete una columna NaN).
  - Nombre: {MOEA}_{MOP}_{m}D_N{N}_R{run}.pof
    ej. MOEAD_DTLZ1_02D_N200_R19.pof == MOEA=MOEAD, MOP=DTLZ1, m=2, N=200, run=19.
"""
from __future__ import annotations

import io
import logging
import re
import zipfile
from typing import Iterator

import numpy as np
import pandas as pd

from domain.model import PFA, ConfigCSV  # unica excepcion permitida (el modelo)

log = logging.getLogger(__name__)

# Patron del nombre
_PATRON_NOMBRE = re.compile(
    r"^(?P<moea>[^_]+)_(?P<mop>[^_]+)_(?P<m>\d+)D_N(?P<n>\d+)_R(?P<corrida>\d+)\.pof$",
    re.IGNORECASE,
)


class ErrorValidacionPFA(ValueError):
    """La forma real del archivo no concuerda con la cabecera o el nombre (N, m)."""


# ─────────────────────────────────────────────────────────────────────────────
#  Utilidades
# ─────────────────────────────────────────────────────────────────────────────
def _basename(ruta) -> str:
    """Ultimo componente de la ruta (sirve para rutas de disco y del zip)."""
    return re.split(r"[\\/]", str(ruta))[-1]


def parsear_nombre(nombre: str) -> dict:
    """
    Extrae (moea, mop, m, n, corrida) del NOMBRE del archivo. Usa el basename, asi
    que ignora la carpeta contenedora del zip. Lanza ValueError si no concuerda con
    el patron {MOEA}_{MOP}_{m}D_N{N}_R{run}.pof.
    """
    base = _basename(nombre)
    coincide = _PATRON_NOMBRE.match(base)
    if coincide is None:
        raise ValueError(
            f"Nombre de archivo no reconocido: '{base}'. Se esperaba el patron "
            "{MOEA}_{MOP}_{m}D_N{N}_R{run}.pof (p. ej. MOEAD_DTLZ1_02D_N200_R19.pof)."
        )
    g = coincide.groupdict()
    return {
        "moea": g["moea"],
        "mop": g["mop"],
        "m": int(g["m"]),
        "n": int(g["n"]),
        "corrida": int(g["corrida"]),
    }


def leer_cabecera(fuente) -> tuple[int, int] | None:
    """
    Lee la 1a linea de 'fuente' (ruta de disco o file-like). Si empieza con '#' y
    trae dos enteros '# N m', devuelve (N, m); si no hay cabecera o no es parseable,
    devuelve None. No consume el resto de la fuente (en file-likes restaura la pos).
    """
    if hasattr(fuente, "read"):  # file-like (BytesIO, stream del zip, ...)
        pos = fuente.tell() if hasattr(fuente, "tell") else None
        primera = fuente.readline()
        if pos is not None:
            fuente.seek(pos)
        if isinstance(primera, bytes):
            primera = primera.decode("utf-8", errors="replace")
    else:  # ruta de disco
        with open(fuente, "r", encoding="utf-8", errors="replace") as fh:
            primera = fh.readline()

    primera = primera.strip()
    if not primera.startswith("#"):
        return None
    partes = primera.lstrip("#").split()
    if len(partes) < 2:
        return None
    try:
        return int(partes[0]), int(partes[1])
    except ValueError:
        return None


def _leer_dataframe(fuente, config: ConfigCSV) -> pd.DataFrame:
    """Lee SOLO los puntos (la cabecera '#' se salta como comentario)."""
    return pd.read_csv(
        fuente,
        sep=config.separador,
        comment=(config.comentario or None),
        header=None,
        engine="python",          # necesario para sep regex r"\s+"
        decimal=config.decimal,
    )


def _exigir_iguales(archivo: str, etiqueta: str, real: int,
                    valor_nombre: int, valor_cabecera: int | None) -> None:
    """
    Falla con ErrorValidacionPFA si 'real', 'nombre' y (si existe) 'cabecera' no
    coinciden, diciendo QUE archivo y QUE tres valores chocan. Nunca recorta/rellena.
    """
    valores = {"real": real, "nombre": valor_nombre}
    if valor_cabecera is not None:
        valores["cabecera"] = valor_cabecera
    if len(set(valores.values())) > 1:
        detalle = ", ".join(f"{k}={v}" for k, v in valores.items())
        raise ErrorValidacionPFA(
            f"'{archivo}': discrepancia en {etiqueta} ({detalle})."
        )


def _construir_pfa(df: pd.DataFrame, nombre: str,
                   cabecera: tuple[int, int] | None, config: ConfigCSV) -> PFA:
    """
    NUCLEO COMPARTIDO (disco y zip): validacion cruzada + construccion del PFA.
    Exige: columnas reales == m(nombre) == m(cabecera?); filas reales == N(nombre)
    == N(cabecera?).
    """
    meta = parsear_nombre(nombre)          # ValueError si el nombre no matchea
    filas, columnas = df.shape
    m_cab = cabecera[1] if cabecera is not None else None
    n_cab = cabecera[0] if cabecera is not None else None
    base = _basename(nombre)

    _exigir_iguales(base, "numero de objetivos (m)", columnas, meta["m"], m_cab)
    _exigir_iguales(base, "numero de puntos (N)", filas, meta["n"], n_cab)

    puntos = df.to_numpy(dtype=float)      # acepta cientifica y negativos
    return PFA(
        moea=meta["moea"], mop=meta["mop"], m=meta["m"], n=meta["n"],
        corrida=meta["corrida"], puntos=puntos, archivo=base,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Lectura de UN archivo
# ─────────────────────────────────────────────────────────────────────────────
def leer_pfa(ruta, config: ConfigCSV | None = None) -> PFA:
    """Lee un .pof desde DISCO (lo usan los archivos sueltos y los tests)."""
    config = config or ConfigCSV.preset_pof()
    cabecera = leer_cabecera(ruta)
    df = _leer_dataframe(ruta, config)
    return _construir_pfa(df, str(ruta), cabecera, config)


def leer_pfa_buffer(fuente, nombre: str, config: ConfigCSV | None = None) -> PFA:
    """
    Lee un .pof desde un FILE-LIKE (lo usa el zip y la subida de la UI). La UI lee
    los bytes y los pasa aqui; la capa de datos nunca ve el objeto de streamlit.
    """
    config = config or ConfigCSV.preset_pof()
    datos = fuente.read()
    if isinstance(datos, str):
        datos = datos.encode(config.encoding)
    cabecera = leer_cabecera(io.BytesIO(datos))
    df = _leer_dataframe(io.BytesIO(datos), config)
    return _construir_pfa(df, nombre, cabecera, config)


# ─────────────────────────────────────────────────────────────────────────────
#  Lectura por LOTES (saltan y REPORTAN los que fallen; no abortan el lote)
# ─────────────────────────────────────────────────────────────────────────────
def _reportar(errores: list | None, nombre: str, exc: Exception) -> None:
    mensaje = str(exc)
    log.warning("PFA omitido '%s': %s", nombre, mensaje)
    if errores is not None:
        errores.append((nombre, mensaje))


def iterar_pofs(rutas, config: ConfigCSV | None = None,
                errores: list | None = None) -> Iterator[PFA]:
    """Genera PFA desde rutas de DISCO; salta y reporta los que fallen."""
    for ruta in rutas:
        try:
            yield leer_pfa(ruta, config)
        except Exception as exc:  # noqa: BLE001 (un .pof malo no debe abortar el lote)
            _reportar(errores, _basename(ruta), exc)


def _es_basura_mac(nombre: str, base: str) -> bool:
    """True para basura que meten los zips hechos en Mac (__MACOSX, '._...')."""
    componentes = re.split(r"[\\/]", nombre)
    return "__MACOSX" in componentes or base.startswith("._")


def _verificar_carpeta(nombre: str, pfa: PFA) -> None:
    """La carpeta contenedora deberia ser el MOEA; si no, solo advierte (no aborta)."""
    componentes = [c for c in re.split(r"[\\/]", nombre) if c]
    if len(componentes) >= 2:
        carpeta = componentes[-2]
        if carpeta.lower() != pfa.moea.lower():
            log.warning(
                "Carpeta '%s' no coincide con el MOEA '%s' del nombre (%s).",
                carpeta, pfa.moea, pfa.archivo,
            )


def _abrir_zip(fuente) -> zipfile.ZipFile:
    """Abre el zip EN MEMORIA desde bytes o un file-like (no extrae a disco)."""
    if isinstance(fuente, (bytes, bytearray)):
        fuente = io.BytesIO(fuente)
    return zipfile.ZipFile(fuente)


def iterar_pofs_zip(zip_fuente, config: ConfigCSV | None = None,
                    errores: list | None = None) -> Iterator[PFA]:
    """
    Genera PFA recorriendo un .zip subido por el usuario (carpetas por MOEA en la
    raiz). Recorre carpetas EXISTAN o no (recursivo, sin profundidad fija), salta
    carpetas vacias, ignora todo lo que no sea .pof y la basura de Mac, valida
    carpeta vs nombre (advertencia) y salta+reporta los .pof que fallen.
    """
    with _abrir_zip(zip_fuente) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            nombre = info.filename
            base = _basename(nombre)
            if not base.lower().endswith(".pof"):
                continue
            if _es_basura_mac(nombre, base):
                continue
            try:
                with zf.open(info) as fh:
                    pfa = leer_pfa_buffer(fh, base, config)
            except Exception as exc:  # noqa: BLE001
                _reportar(errores, base, exc)
                continue
            _verificar_carpeta(nombre, pfa)
            yield pfa
