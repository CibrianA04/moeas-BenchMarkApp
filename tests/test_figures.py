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
# m=4 y m=5 sinteticos y deterministas; la ultima columna incluye NEGATIVOS
# (la normalizacion por columna debe absorberlos sin fallar).
P4 = np.column_stack([np.linspace(0.0, 1.0, 6), np.linspace(1.0, 0.0, 6),
                      np.linspace(0.2, 0.8, 6), np.linspace(5.0, -3.0, 6)])
P5 = np.column_stack([P4, np.linspace(-1.0, 1.0, 6)])


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


def test_figuras_m4_m5_devuelven_figure_del_tipo_correcto():
    # Cada constructora m>3 devuelve un Figure sin lanzar, con el eje esperado.
    esperado = {figures.figura_parallel: "rectilinear",
                figures.figura_radar: "polar",
                figures.figura_bubble: "3d",
                figures.figura_heatmap: "rectilinear"}
    for P in (P4, P5):
        for construir, eje in esperado.items():
            fig = construir(P, titulo="t")
            try:
                assert isinstance(fig, Figure)
                assert fig.axes[0].name == eje
            finally:
                figures.cerrar(fig)


def test_bubble_codifica_f4_en_color_con_colorbar():
    con_color = figures.figura_bubble(P4)         # m>=4: colorbar de $f_4$
    simple = figures.figura_bubble(P3)            # m==3: scatter 3D sin color
    try:
        assert len(con_color.axes) == 2           # eje 3D + eje del colorbar
        assert len(simple.axes) == 1
    finally:
        figures.cerrar(con_color)
        figures.cerrar(simple)


def test_heatmap_es_matriz_con_colorbar():
    fig = figures.figura_heatmap(P5, titulo="t")
    try:
        assert len(fig.axes[0].images) == 1       # el matshow
        assert len(fig.axes) == 2                 # + colorbar
        assert len(fig.axes[0].get_yticks()) == 0
    finally:
        figures.cerrar(fig)


def test_dispatcher_metodo_para_m4_y_m5():
    for P, m in ((P4, 4), (P5, 5)):
        for metodo in figures.METODOS_M4:
            fig = figures.figura_frente(P, m, metodo=metodo, titulo="t")
            try:
                assert isinstance(fig, Figure)
            finally:
                figures.cerrar(fig)
    # Default sin `metodo`: coordenadas paralelas (eje rectilineal con lineas).
    fig = figures.figura_frente(P4, 4)
    try:
        assert fig.axes[0].name == "rectilinear"
        assert len(fig.axes[0].lines) == len(P4)
    finally:
        figures.cerrar(fig)


def test_dispatcher_m2_m3_siguen_igual_e_ignoran_metodo():
    f2 = figures.figura_frente(P2, 2, metodo="Radar")
    f3 = figures.figura_frente(P3, 3, metodo="Heatmap")
    try:
        assert f2.axes[0].name == "rectilinear"   # sigue siendo el scatter 2D
        assert len(f2.axes[0].collections) == 1
        assert f3.axes[0].name == "3d"            # sigue siendo el scatter 3D
    finally:
        figures.cerrar(f2)
        figures.cerrar(f3)


def test_dispatcher_m_mayor_que_3_metodo_desconocido():
    # m>3 ya se atiende con METODOS_M4; un metodo fuera del mapa es ValueError.
    with pytest.raises(ValueError, match="Metodo desconocido"):
        figures.figura_frente(np.zeros((5, 4)), metodo="RadViz")


def test_ninguna_funcion_escribe_a_disco(tmp_path, monkeypatch):
    # A diferencia del script del doc (savefig dentro de plot), aqui construir
    # la figura NO debe tocar el disco: exportar es responsabilidad aparte.
    monkeypatch.chdir(tmp_path)
    f2 = figures.figura_frente_2d(P2, titulo="t")
    f3 = figures.figura_frente_3d(P3, titulo="t")
    figures.cerrar(f2)
    figures.cerrar(f3)
    assert list(tmp_path.iterdir()) == []


def test_guardar_figura_tex_pgf_segun_haya_latex():
    # Con LaTeX instalado: bytes del fragmento PGF; sin LaTeX: None (boton
    # deshabilitado). La rama se decide con hay_latex(), no se hardcodea.
    fig = figures.figura_frente_2d(P2, titulo="t")
    try:
        tex = figures.guardar_figura(fig, "TikZ (.tex)")
        if figures.hay_latex():
            assert tex is not None and len(tex) > 0
            assert tex.startswith(b"%% Creator: Matplotlib, PGF backend")
        else:
            assert tex is None
    finally:
        figures.cerrar(fig)


def test_escala_fuente_sube_el_tamano_del_titulo():
    chico = figures.figura_frente_2d(P2, titulo="t", escala_fuente=1.0)
    grande = figures.figura_frente_2d(P2, titulo="t", escala_fuente=2.0)
    try:
        assert grande._suptitle.get_fontsize() > chico._suptitle.get_fontsize()
    finally:
        figures.cerrar(chico)
        figures.cerrar(grande)
