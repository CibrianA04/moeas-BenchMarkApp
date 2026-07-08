# -*- coding: utf-8 -*-
"""
Tests de la siembra PURA del multiselect de indicadores (Paso 2): al volver al
paso, el widget se re-monta y debe restaurarse desde K_INDS; el default nunca
incluye indicadores sin computo (R2/Riesz/SPD).
"""
from __future__ import annotations

from domain import indicators
from ui.steps.paso_indicadores import _IMPLEMENTADOS, _default_indicadores


def test_persistido_no_vacio_se_restaura_en_su_orden():
    assert _default_indicadores(["IGD", "HV"]) == ["IGD", "HV"]


def test_sin_persistido_cae_a_los_implementados():
    assert _default_indicadores([]) == list(_IMPLEMENTADOS)
    assert _default_indicadores(None) == list(_IMPLEMENTADOS)


def test_nunca_devuelve_ids_no_implementados():
    assert _default_indicadores(["R2", "HV", "Riesz", "SPD"]) == ["HV"]


def test_persistido_solo_con_no_implementados_cae_al_default():
    assert _default_indicadores(["R2", "Riesz"]) == list(_IMPLEMENTADOS)


def test_default_no_contiene_r2_riesz_spd():
    assert not {"R2", "Riesz", "SPD"} & set(_default_indicadores([]))


def test_implementados_existen_en_el_catalogo():
    # Guarda contra typos: todos los ids sembrables estan en el CATALOGO.
    assert set(_IMPLEMENTADOS) <= set(indicators.CATALOGO)
