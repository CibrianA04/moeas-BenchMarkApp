# -*- coding: utf-8 -*-
"""
Tests de la decision PURA de reprocesado del Paso 1 (_debe_reprocesar): el
uploader remontado VACIO no debe pisar los PFAs/frentes ya cargados en
session_state (bug: al volver al Paso 1 se perdia todo lo cargado).
"""
from __future__ import annotations

from ui.steps.paso_datos import _debe_reprocesar

_F1 = (("a.pof", 100),)          # firma de una subida previa
_F2 = (("b.pof", 200),)          # firma de una subida distinta


def test_uploader_vacio_con_datos_previos_no_pisa():
    # Al volver al paso: archivos=[] y firma=() != guardada -> aun asi, conservar.
    assert _debe_reprocesar([], (), _F1, hay_datos=True) is False


def test_uploader_vacio_sin_datos_no_hace_nada():
    assert _debe_reprocesar([], (), None, hay_datos=False) is False


def test_archivos_nuevos_con_firma_distinta_reprocesa():
    assert _debe_reprocesar(["subido"], _F2, _F1, hay_datos=True) is True


def test_mismos_archivos_misma_firma_no_reprocesa():
    assert _debe_reprocesar(["subido"], _F1, _F1, hay_datos=True) is False


def test_archivos_nuevos_sin_datos_previos_reprocesa():
    assert _debe_reprocesar(["subido"], _F1, None, hay_datos=False) is True


def test_misma_firma_pero_estado_vacio_autorrepara():
    # Firma vieja coincide pero el estado quedo vacio (p. ej. un futuro "Nuevo
    # proyecto" que limpie los datos sin limpiar la firma): reprocesar.
    assert _debe_reprocesar(["subido"], _F1, _F1, hay_datos=False) is True
