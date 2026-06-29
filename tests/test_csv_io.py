# -*- coding: utf-8 -*-
"""
Tests del lector de .pof (data/csv_io.py) sobre los 7 archivos reales de
data_ejemplo/, mas casos negativos y un .zip armado en memoria.
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import pytest

from data import csv_io
from data.csv_io import ErrorValidacionPFA

RAIZ = Path(__file__).resolve().parents[1]
EJEMPLOS = RAIZ / "data_ejemplo"

# (nombre, moea, mop, m, n, corrida) — verdad de terreno de los 7 .pof de muestra.
ESPERADOS = [
    ("NSGAII_WFG3_03D_N105_R01.pof",  "NSGAII", "WFG3",  3, 105, 1),
    ("NSGAII_VNT2_03D_N210_R19.pof",  "NSGAII", "VNT2",  3, 210, 19),
    ("NSGAII_DTLZ7_02D_N100_R18.pof", "NSGAII", "DTLZ7", 2, 100, 18),
    ("NSGAII_DTLZ2_02D_N11_R23.pof",  "NSGAII", "DTLZ2", 2, 11, 23),
    ("MOEAD_VNT3_03D_N15_R09.pof",    "MOEAD",  "VNT3",  3, 15, 9),
    ("MOEAD_IMOP7_03D_N78_R22.pof",   "MOEAD",  "IMOP7", 3, 78, 22),
    ("MOEAD_DTLZ1_02D_N200_R19.pof",  "MOEAD",  "DTLZ1", 2, 200, 19),
]


@pytest.mark.parametrize("nombre,moea,mop,m,n,corrida", ESPERADOS)
def test_parsear_nombre(nombre, moea, mop, m, n, corrida):
    assert csv_io.parsear_nombre(nombre) == {
        "moea": moea, "mop": mop, "m": m, "n": n, "corrida": corrida,
    }


def test_parsear_nombre_ignora_carpeta_del_zip():
    # El basename manda aunque venga con la ruta de la carpeta del zip.
    d = csv_io.parsear_nombre("MOEAD/sub/MOEAD_DTLZ1_02D_N200_R19.pof")
    assert d["moea"] == "MOEAD" and d["m"] == 2 and d["corrida"] == 19


@pytest.mark.parametrize("nombre,moea,mop,m,n,corrida", ESPERADOS)
def test_leer_pfa_validacion_cruzada(nombre, moea, mop, m, n, corrida):
    pfa = csv_io.leer_pfa(EJEMPLOS / nombre)
    assert (pfa.moea, pfa.mop, pfa.m, pfa.n, pfa.corrida) == (moea, mop, m, n, corrida)
    assert pfa.archivo == nombre
    assert pfa.puntos.shape == (n, m)          # filas=N, columnas=m
    assert pfa.puntos.dtype == np.float64
    assert not np.isnan(pfa.puntos).any()      # sin columna fantasma por el espacio final


def test_leer_cabecera():
    assert csv_io.leer_cabecera(EJEMPLOS / "MOEAD_DTLZ1_02D_N200_R19.pof") == (200, 2)


def test_admite_valores_negativos():
    # VNT2 tiene objetivos negativos: no se deben recortar ni asumir dominio positivo.
    pfa = csv_io.leer_pfa(EJEMPLOS / "NSGAII_VNT2_03D_N210_R19.pof")
    assert pfa.puntos.min() < 0


# ── Casos negativos ──────────────────────────────────────────────────────────
def test_nombre_mal_formado_lanza_valueerror():
    with pytest.raises(ValueError):
        csv_io.parsear_nombre("archivo_raro.pof")


def test_columnas_no_coinciden_lanza_validacion(tmp_path):
    # El nombre dice 2 objetivos (02D) pero el contenido trae 3 columnas.
    malo = tmp_path / "MOEAD_DTLZ1_02D_N3_R01.pof"
    malo.write_text("# 3 2\n1 2 3 \n4 5 6 \n7 8 9 \n", encoding="utf-8")
    with pytest.raises(ErrorValidacionPFA):
        csv_io.leer_pfa(malo)


def test_filas_no_coinciden_lanza_validacion(tmp_path):
    # El nombre dice N=5 pero solo hay 2 puntos.
    malo = tmp_path / "MOEAD_DTLZ1_02D_N5_R01.pof"
    malo.write_text("# 5 2\n0.1 0.2 \n0.3 0.4 \n", encoding="utf-8")
    with pytest.raises(ErrorValidacionPFA):
        csv_io.leer_pfa(malo)


# ── Ingesta del .zip (estructura real del usuario) ───────────────────────────
def _armar_zip() -> bytes:
    """Zip con MOEAD/ y NSGAII/ (algunos .pof reales), adaW/ VACIA y basura."""
    incluidos = [
        "MOEAD_DTLZ1_02D_N200_R19.pof",
        "MOEAD_VNT3_03D_N15_R09.pof",
        "NSGAII_DTLZ2_02D_N11_R23.pof",
        "NSGAII_WFG3_03D_N105_R01.pof",
    ]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for nombre in incluidos:
            carpeta = nombre.split("_")[0]                 # MOEAD / NSGAII
            zf.writestr(f"{carpeta}/{nombre}", (EJEMPLOS / nombre).read_bytes())
        zf.writestr("adaW/", b"")                          # carpeta vacia -> se ignora
        zf.writestr("README.txt", b"no es un pof")         # basura -> se ignora
        zf.writestr("__MACOSX/._MOEAD_DTLZ1_02D_N200_R19.pof", b"basura mac")
    return buf.getvalue()


def test_iterar_pofs_zip_cuenta_y_filtra():
    errores: list = []
    pfas = list(csv_io.iterar_pofs_zip(_armar_zip(), errores=errores))
    assert len(pfas) == 4                 # solo los .pof validos; ignora vacia y basura
    assert errores == []
    assert {p.archivo for p in pfas} == {
        "MOEAD_DTLZ1_02D_N200_R19.pof", "MOEAD_VNT3_03D_N15_R09.pof",
        "NSGAII_DTLZ2_02D_N11_R23.pof", "NSGAII_WFG3_03D_N105_R01.pof",
    }


def test_iterar_pofs_zip_campos_correctos():
    pfas = {p.archivo: p for p in csv_io.iterar_pofs_zip(_armar_zip())}
    assert pfas["MOEAD_DTLZ1_02D_N200_R19.pof"].n == 200
    assert pfas["MOEAD_DTLZ1_02D_N200_R19.pof"].puntos.shape == (200, 2)
    assert pfas["NSGAII_WFG3_03D_N105_R01.pof"].m == 3
    assert pfas["NSGAII_WFG3_03D_N105_R01.pof"].puntos.shape == (105, 3)


def test_iterar_pofs_zip_reporta_malos_sin_abortar():
    # Mezcla un .pof bueno con uno corrupto (columnas != m): debe cargar 1 y reportar 1.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        bueno = "NSGAII_DTLZ2_02D_N11_R23.pof"
        zf.writestr(f"NSGAII/{bueno}", (EJEMPLOS / bueno).read_bytes())
        zf.writestr("MOEAD/MOEAD_DTLZ1_02D_N3_R01.pof", b"# 3 2\n1 2 3 \n4 5 6 \n7 8 9 \n")
    errores: list = []
    pfas = list(csv_io.iterar_pofs_zip(buf.getvalue(), errores=errores))
    assert len(pfas) == 1
    assert len(errores) == 1
    assert errores[0][0] == "MOEAD_DTLZ1_02D_N3_R01.pof"
