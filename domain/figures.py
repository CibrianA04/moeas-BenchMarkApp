# -*- coding: utf-8 -*-
"""
Construccion HEADLESS de figuras con matplotlib (motor UNICO de graficas).

Importante: se fija el backend 'Agg' (sin ventana), se devuelven objetos Figure
y NO se importa Streamlit. La capa de presentacion hace st.pyplot(fig).
"""
from __future__ import annotations

import io

import matplotlib
matplotlib.use("Agg")            # backend sin pantalla; debe ir antes de pyplot
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np               # noqa: E402

# Metodos de visualizacion disponibles (extensible: agregar = una entrada + su rama).
METODOS = [
    "Dispersion 2D",
    "Dispersion 3D",
    "Coordenadas paralelas",
    "(proximamente) RadViz",
    "(proximamente) Heatmap",
]


def fig_scatter_2d(puntos: np.ndarray, ref: np.ndarray | None = None,
                   titulo: str = "") -> "plt.Figure":
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(puntos[:, 0], puntos[:, 1], s=16, label="PFA")
    if ref is not None:
        orden = np.argsort(ref[:, 0])
        ax.plot(ref[orden, 0], ref[orden, 1], lw=1.2, color="crimson",
                label="referencia")
    ax.set_xlabel("f1")
    ax.set_ylabel("f2")
    ax.set_title(titulo)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    return fig


def fig_scatter_3d(puntos: np.ndarray, titulo: str = "") -> "plt.Figure":
    fig = plt.figure(figsize=(5, 4))
    ax = fig.add_subplot(projection="3d")
    ax.scatter(puntos[:, 0], puntos[:, 1], puntos[:, 2], s=10)
    ax.set_xlabel("f1")
    ax.set_ylabel("f2")
    ax.set_zlabel("f3")
    ax.set_title(titulo)
    fig.tight_layout()
    return fig


def fig_parallel(puntos: np.ndarray, etiquetas: list[str] | None = None,
                 titulo: str = "") -> "plt.Figure":
    n, m = puntos.shape
    etiquetas = etiquetas or [f"f{j + 1}" for j in range(m)]
    mn, mx = puntos.min(0), puntos.max(0)
    rango = np.where(mx > mn, mx - mn, 1.0)
    P = (puntos - mn) / rango           # normaliza por columna a [0,1] para mostrar
    fig, ax = plt.subplots(figsize=(6, 4))
    xs = np.arange(m)
    for i in range(n):
        ax.plot(xs, P[i], lw=0.6, alpha=0.5)
    ax.set_xticks(xs)
    ax.set_xticklabels(etiquetas)
    ax.set_ylim(-0.02, 1.02)
    ax.set_ylabel("valor normalizado")
    ax.set_title(titulo)
    fig.tight_layout()
    return fig


def guardar_figura(fig: "plt.Figure", formato_ui: str) -> bytes | None:
    """
    Exporta la figura a bytes. PNG/SVG/EPS son reales aqui.
    TikZ/.tex devuelve None (FUTURO: requiere tikzplotlib o el backend pgf).
    """
    mapa = {"PNG (prioritario)": "png", "SVG": "svg", "EPS": "eps"}
    fmt = mapa.get(formato_ui)
    if fmt is None:
        return None
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=150, bbox_inches="tight")
    return buf.getvalue()


def cerrar(fig: "plt.Figure") -> None:
    """Libera la figura (evita acumular memoria entre reruns)."""
    plt.close(fig)
