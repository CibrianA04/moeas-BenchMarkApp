# -*- coding: utf-8 -*-
"""
Tests de indicadores (hoy solo HV via pymoo) y de preprocesamiento.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from data import csv_io
from domain import indicators, preprocessing

RAIZ = Path(__file__).resolve().parents[1]
EJEMPLOS = RAIZ / "data_ejemplo"


# ── HV ───────────────────────────────────────────────────────────────────────
def test_hv_caso_analitico_conocido():
    # Minimizacion. Puntos {(0,1),(1,0)}, ref (2,2):
    #   (0,1) cubre [0,2]x[1,2]=2 ; (1,0) cubre [1,2]x[0,2]=2 ; solape 1 -> HV=3.
    P = np.array([[0.0, 1.0], [1.0, 0.0]])
    assert indicators.calcular("HV", P, punto_ref=[2.0, 2.0]) == pytest.approx(3.0)


def test_hv_pof_real_dtlz2():
    # Caso pequeno real (11 puntos) con punto de referencia fijo: valor de regresion.
    pfa = csv_io.leer_pfa(EJEMPLOS / "NSGAII_DTLZ2_02D_N11_R23.pof")
    hv = indicators.calcular("HV", pfa.puntos, punto_ref=[1.1, 1.1])
    assert hv == pytest.approx(0.3659255577, rel=1e-6)


def test_hv_punto_ref_por_defecto_usa_nadir():
    # Sin punto_ref: se toma el nadir del conjunto; debe dar un valor finito >= 0.
    pfa = csv_io.leer_pfa(EJEMPLOS / "NSGAII_DTLZ2_02D_N11_R23.pof")
    hv = indicators.calcular("HV", pfa.puntos)
    assert np.isfinite(hv) and hv >= 0.0


# ── IGD / IGD+ ───────────────────────────────────────────────────────────────
def test_igd_pfa_igual_a_referencia_es_cero():
    # Si el PFA coincide con el frente de referencia, IGD = 0.
    ref = np.array([[0.0, 1.0], [1.0, 0.0], [0.5, 0.5]])
    assert indicators.calcular("IGD", ref.copy(), ref=ref) == pytest.approx(0.0, abs=1e-12)


def test_igdplus_pfa_igual_a_referencia_es_cero():
    # Idem para IGD+.
    ref = np.array([[0.0, 1.0], [1.0, 0.0], [0.5, 0.5]])
    assert indicators.calcular("IGD+", ref.copy(), ref=ref) == pytest.approx(0.0, abs=1e-12)


# ── Eps+ (epsilon aditivo) ───────────────────────────────────────────────────
def test_eps_plus_caso_a_mano():
    # Minimizacion. R = {(0,0)}, A = {(3,1),(1,4)}:
    #   eps para cubrir (0,0): (3,1)->max(3,1)=3 ; (1,4)->max(1,4)=4 ; min=3.
    #   unico r -> eps+ = 3.
    ref = np.array([[0.0, 0.0]])
    P = np.array([[3.0, 1.0], [1.0, 4.0]])
    assert indicators.calcular("Eps+", P, ref=ref) == pytest.approx(3.0)


def test_eps_plus_pfa_igual_a_referencia_es_cero():
    # Frente identico (no dominado) -> eps+ = 0.
    ref = np.array([[0.0, 1.0], [1.0, 0.0]])
    assert indicators.calcular("Eps+", ref.copy(), ref=ref) == pytest.approx(0.0, abs=1e-12)


# ── Dp (Delta p) ─────────────────────────────────────────────────────────────
def test_dp_es_max_de_gd_e_igd():
    from pymoo.indicators.gd import GD
    from pymoo.indicators.igd import IGD
    ref = np.array([[0.0, 1.0], [1.0, 0.0], [0.5, 0.5]])
    P = np.array([[0.1, 0.9], [0.9, 0.1], [0.6, 0.6]])
    esperado = max(float(GD(ref)(P)), float(IGD(ref)(P)))
    assert indicators.calcular("Dp", P, ref=ref) == pytest.approx(esperado)


# ── Dispatch / validacion del catalogo ───────────────────────────────────────
def test_requiere_ref_sin_ref_lanza_valueerror():
    # IGD requiere frente de referencia: sin 'ref' debe fallar claro.
    P = np.zeros((5, 2))
    with pytest.raises(ValueError):
        indicators.calcular("IGD", P)


def test_indicador_no_implementado_lanza_notimplemented():
    # R2 con ref pasa la validacion de requiere_ref pero aun no esta implementado.
    P = np.zeros((5, 2))
    ref = np.ones((5, 2))
    with pytest.raises(NotImplementedError):
        indicators.calcular("R2", P, ref=ref)


def test_indicador_desconocido_lanza_keyerror():
    with pytest.raises(KeyError):
        indicators.calcular("NO_EXISTE", np.zeros((3, 2)))


# ── Preprocesamiento ─────────────────────────────────────────────────────────
def test_filtrar_no_dominadas():
    # (0,0) domina a todos; los duplicados de (0,0) sobreviven (no se dominan).
    P = np.array([[0., 0.], [1., 1.], [0., 1.], [1., 0.], [0., 0.]])
    out = preprocessing.filtrar_no_dominadas(P)
    assert out.tolist() == [[0.0, 0.0], [0.0, 0.0]]


def test_filtrar_no_dominadas_frente_real_subconjunto():
    # Todo punto del resultado debe seguir siendo no dominado (idempotencia).
    pfa = csv_io.leer_pfa(EJEMPLOS / "NSGAII_DTLZ2_02D_N11_R23.pof")
    nd = preprocessing.filtrar_no_dominadas(pfa.puntos)
    assert 0 < nd.shape[0] <= pfa.puntos.shape[0]
    assert preprocessing.filtrar_no_dominadas(nd).shape[0] == nd.shape[0]


def test_eliminar_duplicados():
    P = np.array([[1., 2.], [1., 2.], [3., 4.]])
    assert preprocessing.eliminar_duplicados(P).tolist() == [[1.0, 2.0], [3.0, 4.0]]


def test_ideal_nadir_y_normalizar():
    P = np.array([[0., 10.], [2., 30.]])
    ideal, nadir = preprocessing.estimar_ideal_nadir(P)
    assert ideal.tolist() == [0.0, 10.0]
    assert nadir.tolist() == [2.0, 30.0]
    Pn = preprocessing.normalizar(P, ideal, nadir)
    assert Pn.tolist() == [[0.0, 0.0], [1.0, 1.0]]
