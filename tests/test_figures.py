# -*- coding: utf-8 -*-
"""
Tests del port de Plot2D/Plot3D (domain/figures.figura_frente_*): headless,
sin leer ni escribir archivos, devuelven matplotlib Figure.
"""
from __future__ import annotations

import numpy as np
import pytest
from matplotlib.figure import Figure

from domain import figures

P2 = np.array([[0.0, 1.0], [0.5, 0.5], [1.0, 0.0], [0.2, 0.8]])
P3 = np.array([[0.0, 0.5, 1.0], [0.5, 0.5, 0.5], [1.0, 0.2, 0.0]])


def test_figura_2d_devuelve_figure_con_n_puntos():
    fig = figures.figura_frente_2d(P2, titulo="t")
    try:
        assert isinstance(fig, Figure)
        ax = fig.axes[0]
        assert len(ax.collections) == 1                  # un scatter
        assert ax.collections[0].get_offsets().shape[0] == len(P2)
    finally:
        figures.cerrar(fig)


def test_figura_3d_devuelve_axes_3d():
    fig = figures.figura_frente_3d(P3, titulo="t")
    try:
        assert isinstance(fig, Figure)
        assert fig.axes[0].name == "3d"
    finally:
        figures.cerrar(fig)


def test_dispatcher_infiere_m_de_las_columnas():
    f2 = figures.figura_frente(P2)
    f3 = figures.figura_frente(P3)
    try:
        assert f2.axes[0].name == "rectilinear"          # 2 columnas -> 2D
        assert f3.axes[0].name == "3d"                   # 3 columnas -> 3D
    finally:
        figures.cerrar(f2)
        figures.cerrar(f3)


def test_dispatcher_m_mayor_que_3_no_implementado():
    with pytest.raises(NotImplementedError):
        figures.figura_frente(np.zeros((5, 4)))


def test_ninguna_funcion_escribe_a_disco(tmp_path, monkeypatch):
    # A diferencia del script del doc (savefig dentro de plot), aqui construir
    # la figura NO debe tocar el disco: exportar es responsabilidad aparte.
    monkeypatch.chdir(tmp_path)
    f2 = figures.figura_frente_2d(P2, titulo="t")
    f3 = figures.figura_frente_3d(P3, titulo="t")
    figures.cerrar(f2)
    figures.cerrar(f3)
    assert list(tmp_path.iterdir()) == []


def test_escala_fuente_sube_el_tamano_del_titulo():
    chico = figures.figura_frente_2d(P2, titulo="t", escala_fuente=1.0)
    grande = figures.figura_frente_2d(P2, titulo="t", escala_fuente=2.0)
    try:
        assert grande._suptitle.get_fontsize() > chico._suptitle.get_fontsize()
    finally:
        figures.cerrar(chico)
        figures.cerrar(grande)
