# -*- coding: utf-8 -*-
"""
Persistencia del proyecto en SQLite: snapshot de SESION.
Guarda el estado ACTUAL del proyecto tal cual (PFAs, frentes de referencia del
usuario, seleccion de indicadores y resultados ya evaluados) para retomarlo sin
re-evaluar. NO guarda parametros de calculo (punto de referencia de HV, p de
Dp, ...): la reproducibilidad completa queda fuera de este snapshot.

Esquema una tabla por tipo de dato, un solo archivo .sqlite:
    meta(clave TEXT PK, valor TEXT)   -- nombre, paso, completado, como JSON
    pfa(moea, mop, m, n, corrida, archivo, puntos BLOB)
    frente_ref(mop, m, puntos BLOB)
    resultado(datos TEXT)            
    omitido(datos TEXT)               -
Los ndarray se serializan con np.save (formato .npy: conserva forma y dtype)
dentro de un BLOB. Este modulo trabaja con dicts PLANOS, sin dataclasses: la
conversion de/hacia domain.model vive en la fachada domain/services.py, asi
que aqui no hace falta importar nada de domain.
"""
from __future__ import annotations

import io
import json
import os
import sqlite3
import tempfile
from pathlib import Path

import numpy as np

# Claves del estado que NO van a `meta` (tienen tabla propia).
_CLAVES_TABLA = ("pfas", "frentes_ref", "resultados", "omitidos")
_MSG_INVALIDO = ("El archivo no es un proyecto valido de la app "
                 "(se esperaba un .sqlite generado por 'Guardar proyecto'): {detalle}")


def _blob(puntos) -> bytes:
    """ndarray -> BLOB .npy (conserva forma y dtype; sin pickle)."""
    buf = io.BytesIO()
    np.save(buf, np.asarray(puntos), allow_pickle=False)
    return buf.getvalue()


def _desblob(datos: bytes) -> np.ndarray:
    return np.load(io.BytesIO(datos), allow_pickle=False)


def _volcar(con: sqlite3.Connection, estado: dict) -> None:
    """Escribe el estado completo en la conexion (borra y recrea las tablas)."""
    cur = con.cursor()
    for tabla in ("meta", "pfa", "frente_ref", "resultado", "omitido"):
        cur.execute(f"DROP TABLE IF EXISTS {tabla}")
    cur.execute("CREATE TABLE meta (clave TEXT PRIMARY KEY, valor TEXT)")
    cur.execute("CREATE TABLE pfa (moea TEXT, mop TEXT, m INTEGER, n INTEGER,"
                " corrida INTEGER, archivo TEXT, puntos BLOB)")
    cur.execute("CREATE TABLE frente_ref (mop TEXT, m INTEGER, puntos BLOB)")
    cur.execute("CREATE TABLE resultado (datos TEXT)")
    cur.execute("CREATE TABLE omitido (datos TEXT)")

    meta = {k: v for k, v in estado.items() if k not in _CLAVES_TABLA}
    cur.executemany("INSERT INTO meta VALUES (?, ?)",
                    [(k, json.dumps(v)) for k, v in meta.items()])
    cur.executemany(
        "INSERT INTO pfa VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(p["moea"], p["mop"], int(p["m"]), int(p["n"]), int(p["corrida"]),
          p.get("archivo", ""), _blob(p["puntos"]))
         for p in estado.get("pfas", [])])
    cur.executemany(
        "INSERT INTO frente_ref VALUES (?, ?, ?)",
        [(f["mop"], int(f["m"]), _blob(f["puntos"]))
         for f in estado.get("frentes_ref", [])])
    cur.executemany("INSERT INTO resultado VALUES (?)",
                    [(json.dumps(r),) for r in estado.get("resultados", [])])
    cur.executemany("INSERT INTO omitido VALUES (?)",
                    [(json.dumps(o),) for o in estado.get("omitidos", [])])
    con.commit()


def _leer(con: sqlite3.Connection) -> dict:
    """Reconstruye el dict de estado desde una conexion abierta. Un archivo que
    no sea un snapshot (corrupto, sin tablas) produce ValueError claro."""
    cur = con.cursor()
    try:
        estado = {clave: json.loads(valor) for clave, valor
                  in cur.execute("SELECT clave, valor FROM meta")}
        estado["pfas"] = [
            {"moea": moea, "mop": mop, "m": m, "n": n, "corrida": corrida,
             "archivo": archivo, "puntos": _desblob(puntos)}
            for moea, mop, m, n, corrida, archivo, puntos in cur.execute(
                "SELECT moea, mop, m, n, corrida, archivo, puntos FROM pfa")]
        estado["frentes_ref"] = [
            {"mop": mop, "m": m, "puntos": _desblob(puntos)}
            for mop, m, puntos in cur.execute(
                "SELECT mop, m, puntos FROM frente_ref")]
        estado["resultados"] = [json.loads(d) for (d,) in
                                cur.execute("SELECT datos FROM resultado")]
        estado["omitidos"] = [json.loads(d) for (d,) in
                              cur.execute("SELECT datos FROM omitido")]
    except (sqlite3.DatabaseError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(_MSG_INVALIDO.format(detalle=exc)) from exc
    return estado


def guardar(estado: dict, ruta) -> None:
    """Vuelca el snapshot de sesion `estado` (dict plano) al archivo `ruta`."""
    con = sqlite3.connect(ruta)
    try:
        _volcar(con, estado)
    finally:
        con.close()


def cargar(ruta) -> dict:
    """Lee el snapshot desde `ruta`. FileNotFoundError si no existe; ValueError
    claro si el archivo no es un snapshot valido (nunca un crash criptico)."""
    if not Path(ruta).is_file():
        raise FileNotFoundError(f"No existe el archivo de proyecto '{ruta}'.")
    con = sqlite3.connect(ruta)
    try:
        return _leer(con)
    finally:
        con.close()


def a_bytes(estado: dict) -> bytes:
    """Snapshot como BYTES .sqlite (para ofrecerlo como descarga: en Streamlit
    Cloud el disco es efimero, no sirve una ruta fija del servidor)."""
    con = sqlite3.connect(":memory:")
    try:
        if hasattr(con, "serialize"):        # Python >= 3.11
            _volcar(con, estado)
            return con.serialize()
    finally:
        con.close()
    # Python < 3.11: via archivo temporal.
    fd, ruta = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        guardar(estado, ruta)
        return Path(ruta).read_bytes()
    finally:
        os.unlink(ruta)


def desde_bytes(datos) -> dict:
    """Snapshot desde BYTES subidos (upload de la UI). ValueError claro si los
    bytes no son un snapshot valido."""
    datos = bytes(datos)
    con = sqlite3.connect(":memory:")
    try:
        if hasattr(con, "deserialize"):      # Python >= 3.11
            try:
                con.deserialize(datos)
            except sqlite3.Error as exc:
                raise ValueError(_MSG_INVALIDO.format(detalle=exc)) from exc
            return _leer(con)
    finally:
        con.close()
    # Python < 3.11: via archivo temporal.
    fd, ruta = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        Path(ruta).write_bytes(datos)
        return cargar(ruta)
    finally:
        os.unlink(ruta)
