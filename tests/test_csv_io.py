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


# ── Cargador de frentes de REFERENCIA (MOEA-visualization-main/data/) ─────────
def test_nombre_frente_referencia_y_mapeo():
    assert csv_io.nombre_frente_referencia("DTLZ2", 3) == ("DTLZ2_03D.pof", "DTLZ2")
    # Mapeo por defecto VNT2->VIE2, VNT3->VIE3 (PENDIENTE confirmar con el doc).
    assert csv_io.nombre_frente_referencia("VNT2", 3) == ("VIE2_03D.pof", "VIE2")
    assert csv_io.nombre_frente_referencia("VNT3", 3) == ("VIE3_03D.pof", "VIE3")


def test_leer_frente_referencia_exacto():
    ref = csv_io.leer_frente_referencia("DTLZ2", 3)
    assert ref.ndim == 2 and ref.shape[1] == 3 and ref.shape[0] > 0


def test_leer_frente_referencia_mapea_vnt_a_vie():
    # VNT2 no tiene archivo propio: debe leer VIE2_03D.pof (300 puntos, 3 obj).
    ref = csv_io.leer_frente_referencia("VNT2", 3)
    assert ref.shape == (300, 3)
    assert ref.min() < 0          # VIE2 tiene objetivos negativos


def test_leer_frente_referencia_inexistente_lanza_filenotfound():
    # IMOP3 solo existe en 02D: pedir 03D no debe sustituir por uno aproximado.
    with pytest.raises(FileNotFoundError):
        csv_io.leer_frente_referencia("IMOP3", 3)


def test_leer_frente_referencia_rechaza_demo():
    # Un prefijo de demo (SLD/INV_SLD/LINEAR) no es frente de referencia valido.
    with pytest.raises(ValueError):
        csv_io.leer_frente_referencia("SLD", 2)


def test_cobertura_frentes_referencia():
    filas = {(f["mop"], f["m"]): f for f in csv_io.cobertura_frentes_referencia(
        [("DTLZ2", 3), ("VNT2", 3), ("IMOP3", 3)])}
    assert filas[("DTLZ2", 3)]["disponible"] is True
    assert filas[("VNT2", 3)]["disponible"] is True       # via VIE2_03D
    assert filas[("VNT2", 3)]["mop_ref"] == "VIE2"
    assert filas[("IMOP3", 3)]["disponible"] is False      # IMOP3 solo en 02D


# ── Frentes de referencia SUBIDOS por el usuario (.zip, prioridad opcion A) ───
def _armar_zip_frentes() -> bytes:
    """Zip de frentes de referencia: uno valido y uno con nombre invalido."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        # Valido: TOKEN del usuario (VNT2, NO VIE2), suelto en la raiz, 3 objetivos.
        zf.writestr("VNT2_03D.pof", b"# 2 3\n1.0 2.0 3.0 \n4.0 5.0 6.0 \n")
        # Valido tambien dentro de data/.
        zf.writestr("data/DTLZ2_03D.pof", b"# 1 3\n7.0 8.0 9.0 \n")
        # Nombre invalido: no casa {MOP}_{m:02d}D.pof -> se omite y reporta.
        zf.writestr("frente_malo.pof", b"# 1 2\n0.1 0.2 \n")
    return buf.getvalue()


def test_leer_frentes_de_zip_toma_valido_y_reporta_invalido():
    frentes, omitidos = csv_io.leer_frentes_de_zip(_armar_zip_frentes())
    assert set(frentes) == {("VNT2", 3), ("DTLZ2", 3)}  # token del usuario, sin mapear
    assert frentes[("VNT2", 3)].shape == (2, 3)
    assert frentes[("DTLZ2", 3)].shape == (1, 3)
    assert [nombre for nombre, _ in omitidos] == ["frente_malo.pof"]


def test_leer_frente_referencia_override_gana_al_automatico():
    frentes, _ = csv_io.leer_frentes_de_zip(_armar_zip_frentes())
    # Con override: VNT2 usa el frente del usuario (2,3), NO el automatico VIE2 (300,3).
    ref = csv_io.leer_frente_referencia("VNT2", 3, override=frentes)
    assert ref.shape == (2, 3)
    assert np.array_equal(ref, frentes[("VNT2", 3)])
    # Sin override sigue cayendo al automatico VIE2_03D (300,3): no rompe lo de hoy.
    assert csv_io.leer_frente_referencia("VNT2", 3).shape == (300, 3)


def test_cobertura_reporta_origen_usuario_vs_automatico():
    frentes, _ = csv_io.leer_frentes_de_zip(_armar_zip_frentes())
    filas = {(f["mop"], f["m"]): f for f in csv_io.cobertura_frentes_referencia(
        [("VNT2", 3), ("DTLZ7", 3)], override=frentes)}
    assert filas[("VNT2", 3)]["origen"] == "usuario"       # subido por el usuario
    assert filas[("VNT2", 3)]["disponible"] is True
    assert filas[("VNT2", 3)]["mop_ref"] == "VNT2"         # emparejo directo, sin mapeo
    assert filas[("DTLZ7", 3)]["origen"] == "automatico"   # no esta en el zip
    assert filas[("DTLZ7", 3)]["disponible"] is True


# ── Override con el nombre del doc (VIE2/VIE3 deben emparejar VNT2/VNT3) ──────
def test_override_con_nombre_del_doc_vie_empareja_vnt(tmp_path):
    # El doc nombra estos frentes VIE2_03D.pof: subido asi, queda con clave
    # ("VIE2", 3) y ANTES no emparejaba con el escenario VNT2 (bug).
    puntos = np.array([[-1.0, -2.0, -3.0], [-4.0, -5.0, -6.0]])
    # dir_ref = carpeta vacia: si el override no emparejara, seria FileNotFoundError.
    ref = csv_io.leer_frente_referencia("VNT2", 3, dir_ref=tmp_path,
                                        override={("VIE2", 3): puntos})
    assert np.array_equal(ref, puntos)


def test_override_directo_sin_mapeo_no_regresa(tmp_path):
    # Un MOP sin mapeo (DTLZ1) sigue emparejando por su clave literal.
    puntos = np.array([[0.0, 1.0], [1.0, 0.0]])
    ref = csv_io.leer_frente_referencia("DTLZ1", 2, dir_ref=tmp_path,
                                        override={("DTLZ1", 2): puntos})
    assert np.array_equal(ref, puntos)


def test_override_clave_literal_gana_a_la_mapeada(tmp_path):
    directo = np.array([[1.0, 1.0, 1.0]])
    mapeado = np.array([[2.0, 2.0, 2.0]])
    ref = csv_io.leer_frente_referencia(
        "VNT2", 3, dir_ref=tmp_path,
        override={("VNT2", 3): directo, ("VIE2", 3): mapeado})
    assert np.array_equal(ref, directo)


def test_cobertura_vnt_disponible_via_override_vie():
    filas = {(f["mop"], f["m"]): f for f in csv_io.cobertura_frentes_referencia(
        [("VNT2", 3)], override={("VIE2", 3): np.array([[-1.0, -2.0, -3.0]])})}
    fila = filas[("VNT2", 3)]
    assert fila["disponible"] is True
    assert fila["origen"] == "usuario"
    assert fila["mop_ref"] == "VIE2"                       # emparejo por la clave mapeada
    assert fila["archivo"] == "VIE2_03D.pof"


# ── Rendimiento: motor C de pandas y cache de frentes de referencia ───────────
def test_leer_pfa_motor_c_sin_columna_nan(tmp_path):
    # Espacio FINAL en cada linea (formato real de los .pof) + notacion
    # cientifica: el motor C con sep=r"\s+" no debe meter columna NaN ni
    # caer al motor python (ParserWarning -> error).
    import warnings
    ruta = tmp_path / "A_DTLZ2_02D_N3_R01.pof"
    ruta.write_text("# 3 2\n0.1 0.9 \n0.5 0.5 \n0.9 1.0e-01 \n", encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("error")                 # cualquier warning = fallo
        pfa = csv_io.leer_pfa(ruta)
    assert pfa.puntos.shape == (3, 2)                  # misma forma que antes
    assert not np.isnan(pfa.puntos).any()              # sin columna NaN fantasma
    assert pfa.puntos[2, 1] == pytest.approx(0.1)      # cientifica y valores OK


def test_cache_frente_referencia_no_reparsea(monkeypatch):
    csv_io._CACHE_FRENTES.clear()
    llamadas = {"n": 0}
    original = csv_io.pd.read_csv

    def contado(*args, **kwargs):
        llamadas["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(csv_io.pd, "read_csv", contado)
    r1 = csv_io.leer_frente_referencia("DTLZ2", 3)
    r2 = csv_io.leer_frente_referencia("DTLZ2", 3)     # misma ruta -> cache
    assert llamadas["n"] == 1
    assert np.array_equal(r1, r2)
    csv_io.leer_frente_referencia("DTLZ2", 2)          # otra ruta -> otra lectura
    assert llamadas["n"] == 2
    csv_io._CACHE_FRENTES.clear()
