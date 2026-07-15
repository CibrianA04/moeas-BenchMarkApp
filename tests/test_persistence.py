# -*- coding: utf-8 -*-
"""
Tests del snapshot SQLite de sesion: round-trip de data/persistence (dicts
planos + ndarrays como BLOB .npy) y de la fachada domain/services (PFA como
dataclasses, carga desde ruta y desde bytes). HEADLESS: sin streamlit.
"""
from __future__ import annotations

import numpy as np
import pytest

from data import persistence
from domain import services
from domain.model import PFA


def _estado_completo() -> dict:
    """Estado plano estilo 'guardado en Paso 3' (con resultados y omitidos)."""
    return {
        "nombre": "exp1", "paso": 2, "completado": [True, True, True, False],
        "separador": "Coma  ( , )", "decimal": "Punto  ( . )",
        "indicadores": ["HV", "IGD"],
        "pfas": [
            {"moea": "NSGAII", "mop": "DTLZ2", "m": 2, "n": 100, "corrida": 1,
             "archivo": "NSGAII_DTLZ2_02D_N100_R01.pof",
             "puntos": np.arange(10, dtype=float).reshape(5, 2)},
            {"moea": "MOEAD", "mop": "WFG3", "m": 3, "n": 105, "corrida": 7,
             "archivo": "",
             "puntos": np.linspace(-1, 1, 12, dtype=np.float32).reshape(4, 3)},
        ],
        "frentes_ref": [{"mop": "DTLZ2", "m": 2, "puntos": np.eye(3, 2)}],
        "resultados": [
            {"mop": "DTLZ2", "m": 2, "N": 100, "moea": "NSGAII",
             "indicador": "HV", "valores": [0.5, 0.6, 0.7]},
        ],
        "omitidos": [
            {"tipo": "sin_referencia", "mop": "IMOP3", "m": 3, "N": 50,
             "indicadores_omitidos": ["IGD"], "motivo": "no existe el frente"},
        ],
    }


# ── data/persistence: round-trip y errores ───────────────────────────────────
def test_round_trip_completo(tmp_path):
    ruta = tmp_path / "proy.sqlite"
    estado = _estado_completo()
    persistence.guardar(estado, ruta)
    cargado = persistence.cargar(ruta)

    assert cargado["nombre"] == "exp1"
    assert cargado["paso"] == 2
    assert cargado["completado"] == [True, True, True, False]
    assert cargado["indicadores"] == ["HV", "IGD"]
    assert cargado["separador"] == "Coma  ( , )"

    # ndarrays identicos: mismos valores, forma y dtype (incluye float32).
    assert len(cargado["pfas"]) == 2
    for orig, vuelto in zip(estado["pfas"], cargado["pfas"]):
        assert np.array_equal(orig["puntos"], vuelto["puntos"])
        assert vuelto["puntos"].shape == orig["puntos"].shape
        assert vuelto["puntos"].dtype == orig["puntos"].dtype
        for campo in ("moea", "mop", "m", "n", "corrida", "archivo"):
            assert vuelto[campo] == orig[campo]

    assert len(cargado["frentes_ref"]) == 1
    assert np.array_equal(cargado["frentes_ref"][0]["puntos"], np.eye(3, 2))
    assert cargado["resultados"] == estado["resultados"]
    assert cargado["omitidos"] == estado["omitidos"]


def test_cargar_inexistente_da_error_claro(tmp_path):
    with pytest.raises(FileNotFoundError, match="No existe el archivo"):
        persistence.cargar(tmp_path / "no_esta.sqlite")


def test_cargar_corrupto_da_error_claro(tmp_path):
    ruta = tmp_path / "roto.sqlite"
    ruta.write_bytes(b"esto no es un sqlite para nada " * 4)
    with pytest.raises(ValueError, match="proyecto valido"):
        persistence.cargar(ruta)


def test_bytes_corruptos_dan_error_claro():
    with pytest.raises(ValueError, match="proyecto valido"):
        persistence.desde_bytes(b"tampoco es un sqlite " * 8)


def test_snapshot_de_paso1_sin_indicadores_ni_resultados(tmp_path):
    # Guardado en Paso 1: solo PFAs (y ni un frente); nada mas es exigible.
    ruta = tmp_path / "p1.sqlite"
    estado = {"nombre": "solo_datos", "paso": 0,
              "completado": [True, False, False, False],
              "pfas": [{"moea": "A", "mop": "B", "m": 2, "n": 4, "corrida": 0,
                        "puntos": np.zeros((4, 2))}]}
    persistence.guardar(estado, ruta)
    cargado = persistence.cargar(ruta)
    assert cargado["nombre"] == "solo_datos"
    assert "indicadores" not in cargado           # la clave nunca se invento
    assert cargado["resultados"] == [] and cargado["omitidos"] == []
    assert np.array_equal(cargado["pfas"][0]["puntos"], np.zeros((4, 2)))


# ── domain/services: fachada con dataclasses ─────────────────────────────────
def _estado_ui() -> dict:
    """Estado como lo arma la sidebar: PFA dataclasses y frentes por (mop, m)."""
    return {
        "nombre": "exp", "paso": 1, "completado": [True, False, False, False],
        "indicadores": ["HV"],
        "pfas": [PFA(moea="NSGAII", mop="DTLZ2", m=2, n=3, corrida=5,
                     puntos=np.array([[0.0, 1.0], [0.5, 0.5], [1.0, 0.0]]),
                     archivo="NSGAII_DTLZ2_02D_N3_R05.pof")],
        "frentes_ref": {("DTLZ2", 2): np.eye(2)},
        "resultados": [], "omitidos": [],
    }


def test_services_round_trip_reconstruye_dataclasses(tmp_path):
    ruta = tmp_path / "proy.sqlite"
    estado = _estado_ui()
    services.guardar_proyecto(estado, ruta)
    vuelto = services.cargar_proyecto(ruta)

    assert isinstance(vuelto["pfas"][0], PFA)
    original = estado["pfas"][0]
    assert (vuelto["pfas"][0].moea, vuelto["pfas"][0].corrida,
            vuelto["pfas"][0].archivo) == (original.moea, original.corrida,
                                           original.archivo)
    assert np.array_equal(vuelto["pfas"][0].puntos, original.puntos)
    assert set(vuelto["frentes_ref"]) == {("DTLZ2", 2)}
    assert np.array_equal(vuelto["frentes_ref"][("DTLZ2", 2)], np.eye(2))
    assert vuelto["indicadores"] == ["HV"]


def test_services_guarda_y_carga_desde_bytes():
    # El flujo real de la UI: descarga (bytes) -> upload (bytes).
    datos = services.proyecto_a_bytes(_estado_ui())
    assert isinstance(datos, bytes) and len(datos) > 0
    vuelto = services.cargar_proyecto(datos)
    assert vuelto["nombre"] == "exp"
    assert isinstance(vuelto["pfas"][0], PFA)
    assert np.array_equal(vuelto["pfas"][0].puntos,
                          _estado_ui()["pfas"][0].puntos)
