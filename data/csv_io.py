# -*- coding: utf-8 -*-
"""
Lectura de archivos .pof (PFA) desde disco y desde un .zip subido por el usuario.


Formato .pof
  - Linea 1 = cabecera '# N m' (N puntos, m objetivos). 
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
from pathlib import Path
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
    """La forma real del archivo no concuerda con la cabecera o el nombre"""


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
    Lee la 1a linea de 'fuente' (ruta de disco o file-like). si no hay cabecera o no es parseable,
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
    """Lee SOLO los puntos """
    # Motor C de pandas (default): soporta sep=r"\s+" de forma NATIVA, sin
    # fallback ni ParserWarning, y es ~6x mas rapido que engine="python".
    return pd.read_csv(
        fuente,
        sep=config.separador,
        comment=(config.comentario or None),
        header=None,
        decimal=config.decimal,
    )


def _exigir_iguales(archivo: str, etiqueta: str, real: int,
                    valor_nombre: int, valor_cabecera: int | None) -> None:
    """
    Falla con ErrorValidacionPFA si 'real', 'nombre' y 'cabecera' no
    coinciden, diciendo QUE archivo y QUE tres valores chocan.
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
    NUCLEO COMPARTIDO (disco y zip): validacion cruzada + construccion del PFA
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
    los bytes y los pasa aqui, la capa de datos nunca ve el objeto de streamlit.
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
    """Genera PFA desde rutas de Disco, salta y reporta los que fallen."""
    for ruta in rutas:
        try:
            yield leer_pfa(ruta, config)
        except Exception as exc:  # noqa: BLE001 (un .pof malo no debe abortar el lote)
            _reportar(errores, _basename(ruta), exc)


def _es_basura_mac(nombre: str, base: str) -> bool:
    """True para basura que meten los zips hechos"""
    componentes = re.split(r"[\\/]", nombre)
    return "__MACOSX" in componentes or base.startswith("._")


def _verificar_carpeta(nombre: str, pfa: PFA) -> None:
    """La carpeta contenedora deberia ser el MOEA, si no, solo advierte."""
    componentes = [c for c in re.split(r"[\\/]", nombre) if c]
    if len(componentes) >= 2:
        carpeta = componentes[-2]
        if carpeta.lower() != pfa.moea.lower():
            log.warning(
                "Carpeta '%s' no coincide con el MOEA '%s' del nombre (%s).",
                carpeta, pfa.moea, pfa.archivo,
            )


def _abrir_zip(fuente) -> zipfile.ZipFile:
    """Abre el zip EN Memoria desde bytes (no extrae a disco)."""
    if isinstance(fuente, (bytes, bytearray)):
        fuente = io.BytesIO(fuente)
    return zipfile.ZipFile(fuente)


def iterar_pofs_zip(zip_fuente, config: ConfigCSV | None = None,
                    errores: list | None = None) -> Iterator[PFA]:
    """
    Genera PFA recorriendo un .zip subido por el usuario (carpetas por MOEA en la
    raiz). Recorre carpetas existan o no (recursivo), salta
    carpetas vacias, ignora todo lo que no sea .pof, valida
    carpeta vs nombre y reporta los .pof que fallen.
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


# ─────────────────────────────────────────────────────────────────────────────
#  Frentes de REFERENCIA 
#
#  Solo valen los que tienen el patron
#  EXACTO {MOP}_{m:02d}D.pof. Los *_sf_*, SLD_*, INV_SLD_*, LINEAR_* se rechazan.
# ─────────────────────────────────────────────────────────────────────────────
# Carpeta por defecto (relativa a la raiz del repo: data/csv_io.py -> raiz).
DIR_FRENTES_REF = Path(__file__).resolve().parents[1] / "MOEA-visualization-main" / "data"

# Cache de frentes de referencia LEIDOS DE DISCO, por ruta resuelta: el motor
# pedia el mismo frente (~10k puntos) escenario tras escenario y se reparseaba
# cada vez. Solo se cachean lecturas EXITOSAS (nunca None ni errores); si cambia
# la ruta (otro dir_ref), cambia la clave sola. El override del usuario ya vive
# en memoria y NO pasa por aqui. Los llamadores tratan el ndarray como solo
# lectura (los indicadores no lo mutan).
_CACHE_FRENTES: dict[str, np.ndarray] = {}

# Mapeo de nombre de MOP -> nombre del archivo de referencia. 
# (VNT2/VNT3 no tienen archivo propio; se usan VIE2/VIE3).
MAPEO_MOP_REF_DEFAULT = {"VNT2": "VIE2", "VNT3": "VIE3"}

# Patron EXACTO de un frente de referencia: un solo guion bajo, sin sufijos.
# Captura (mop, m) para poder reutilizarlo al emparejar por nombre (disco y zip).
_PATRON_REF = re.compile(r"^(?P<mop>[A-Za-z0-9]+)_(?P<m>[0-9]{2})D\.pof$")
_PREFIJOS_DEMO = ("SLD_", "INV_SLD_", "LINEAR_")


def nombre_frente_referencia(mop: str, m: int, mapeo: dict | None = None) -> tuple[str, str]:
    """Construye (nombre_archivo, mop_ref) para (MOP, m) Aplica el mapeo de nombres."""
    mapeo = MAPEO_MOP_REF_DEFAULT if mapeo is None else mapeo
    mop_ref = mapeo.get(mop, mop)
    return f"{mop_ref}_{m:02d}D.pof", mop_ref


def _clave_override(override: dict | None, mop: str, m: int,
                    mapeo: dict | None) -> tuple[str, int] | None:
    """
    Clave con la que (MOP, m) empareja en el override del usuario, o None.

    Prueba primero el token REAL (p. ej. VNT2) y despues el MAPEADO (VIE2): 
    La clave literal tiene prioridad.
    """
    if override is None:
        return None
    if (mop, m) in override:
        return (mop, m)
    mapeo = MAPEO_MOP_REF_DEFAULT if mapeo is None else mapeo
    clave = (mapeo.get(mop, mop), m)
    return clave if clave in override else None


def _leer_puntos_ref(fuente, nombre: str, m: int,
                     config: ConfigCSV) -> np.ndarray:
    """
    Lee los puntos de UN frente de referencia (ruta de disco o file-like del zip)
    REUTILIZANDO el parser .pof del modulo (_leer_dataframe: salta la cabecera '#')
    y valida que tenga m columnas. Nucleo compartido por disco y zip.
    """
    df = _leer_dataframe(fuente, config)
    if df.shape[1] != m:
        raise ErrorValidacionPFA(
            f"'{nombre}': el frente de referencia tiene {df.shape[1]} columnas, "
            f"se esperaban m={m}."
        )
    return df.to_numpy(dtype=float)


def leer_frentes_de_zip(datos_zip, config: ConfigCSV | None = None,
                        ) -> tuple[dict[tuple[str, int], np.ndarray], list]:
    """
    Lee frentes de referencia SUBIDOS por el usuario en un .zip.

        Estructura esperada: archivos .pof sueltos en la raiz del zip o dentro de una
        carpeta `data/`, con el patron EXACTO {MOP}_{m:02d}D.pof (el mismo de
        `nombre_frente_referencia`).
    El MOP de la clave es el token del NOMBRE del archivo tal cual (p. ej. VIE2 si
    asi se llama). Al RESOLVER el override (leer_frente_referencia / cobertura) se
    prueba tambien la clave mapeada: un VIE2_03D.pof subido empareja con VNT2.

    Devuelve ({(MOP, m): puntos}, omitidos), donde omitidos es una lista de
    (nombre, motivo). Un archivo malo se OMITE y REPORTA, no aborta el lote:
        - no .pof / basura de Mac -> se ignoran en silencio;
        - .pof fuera de la raiz o de `data/`, con nombre invalido o prefijo de demo ->
            omitido con motivo;
    - .pof que no se puede leer o cuyas columnas != m -> omitido con motivo.
    """
    config = config or ConfigCSV.preset_pof()
    frentes: dict[tuple[str, int], np.ndarray] = {}
    omitidos: list = []
    with _abrir_zip(datos_zip) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            nombre = info.filename
            base = _basename(nombre)
            if not base.lower().endswith(".pof"):
                continue                       # no es .pof -> se ignora
            if _es_basura_mac(nombre, base):
                continue                       # basura de Mac -> se ignora
            componentes = [c for c in re.split(r"[\\/]", nombre) if c]
            if len(componentes) > 1 and componentes[0].lower() != "data":
                _reportar(omitidos, base, ValueError(
                    "frente en subcarpeta; deben ir en la raiz del zip o dentro de data/"))
                continue
            coincide = _PATRON_REF.match(base)
            if base.startswith(_PREFIJOS_DEMO) or coincide is None:
                _reportar(omitidos, base, ValueError(
                    "nombre invalido; se espera el patron {MOP}_{m:02d}D.pof "
                    "sin sufijos ni prefijos de demo"))
                continue
            mop, m = coincide.group("mop"), int(coincide.group("m"))
            try:
                with zf.open(info) as fh:
                    puntos = _leer_puntos_ref(io.BytesIO(fh.read()), base, m, config)
            except Exception as exc:  # noqa: BLE001 (uno malo no aborta el lote)
                _reportar(omitidos, base, exc)
                continue
            frentes[(mop, m)] = puntos
    return frentes, omitidos


def leer_frente_referencia(mop: str, m: int, dir_ref=None,
                           mapeo: dict | None = None,
                           config: ConfigCSV | None = None,
                           override: dict[tuple[str, int], np.ndarray] | None = None,
                           ) -> np.ndarray:
    """
    Lee el frente de referencia de (MOP, m) -> matriz (R, m).

    - PRIORIDAD del usuario (opcion A): si `override` trae (mop, m) o la clave
      MAPEADA (mop_ref, m)
      devuelve ESE frente (el subido por el usuario)
    - Si no, cae a la carpeta automatica como hoy (con mapeo VNT->VIE): acepta
      UNICAMENTE el patron exacto {MOP}_{m:02d}D.pof (rechaza sufijos y los prefijos
      de demo SLD_/INV_SLD_/LINEAR_). Si el archivo exacto no existe, lanza
      FileNotFoundError
    """
    clave = _clave_override(override, mop, m, mapeo)
    if clave is not None:
        return np.asarray(override[clave], dtype=float)

    dir_ref = Path(dir_ref) if dir_ref is not None else DIR_FRENTES_REF
    nombre, _ = nombre_frente_referencia(mop, m, mapeo)

    if nombre.startswith(_PREFIJOS_DEMO) or _PATRON_REF.match(nombre) is None:
        raise ValueError(
            f"'{nombre}' no es un frente de referencia valido (se exige el patron "
            "exacto {MOP}_{m:02d}D.pof, sin sufijos ni prefijos de demo)."
        )

    ruta = dir_ref / nombre
    if not ruta.is_file():
        raise FileNotFoundError(
            f"No existe frente de referencia exacto para (MOP={mop}, m={m}): se "
            f"busco '{nombre}' en {dir_ref}. No se sustituye por uno aproximado."
        )

    clave_cache = str(ruta.resolve())
    if clave_cache in _CACHE_FRENTES:
        return _CACHE_FRENTES[clave_cache]

    config = config or ConfigCSV.preset_pof()
    puntos = _leer_puntos_ref(ruta, nombre, m, config)
    _CACHE_FRENTES[clave_cache] = puntos          # solo lecturas exitosas
    return puntos


def cobertura_frentes_referencia(pares, dir_ref=None,
                                 mapeo: dict | None = None,
                                 override: dict[tuple[str, int], np.ndarray] | None = None,
                                 ) -> list[dict]:
    """
    Dado un iterable de (MOP, m), reporta cuales tienen frente de referencia.
    Devuelve una lista {mop, m, mop_ref, archivo, disponible, origen}.
    `origen` es "usuario" o "automatico". Para los del usuario, mop_ref es la
    clave con la que emparejo el override: el token real si coincide directo, o
    el MAPEADO (p. ej. VIE2 para VNT2) si el archivo se subio con el nombre.
    """
    dir_ref = Path(dir_ref) if dir_ref is not None else DIR_FRENTES_REF
    filas = []
    for mop, m in pares:
        clave = _clave_override(override, mop, m, mapeo)
        if clave is not None:
            mop_ref = clave[0]
            filas.append({
                "mop": mop, "m": m, "mop_ref": mop_ref,
                "archivo": f"{mop_ref}_{m:02d}D.pof",
                "disponible": True, "origen": "usuario",
            })
            continue
        nombre, mop_ref = nombre_frente_referencia(mop, m, mapeo)
        filas.append({
            "mop": mop, "m": m, "mop_ref": mop_ref, "archivo": nombre,
            "disponible": (dir_ref / nombre).is_file(), "origen": "automatico",
        })
    return filas
