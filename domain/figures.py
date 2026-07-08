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


# ─────────────────────────────────────────────────────────────────────────────
#  Port de Plot2D/Plot3D de MOEA-visualization-main (estilo del doc, HEADLESS).
#
#  Diferencias deliberadas con el script original:
#  - Reciben puntos YA parseados (ndarray (n, m)); NO leen archivos (el set_data
#    del doc usaba delimiter=" " + skiprows=1: columna NaN y cabecera '#' mal).
#  - Devuelven un Figure; NO hacen savefig/show (exportar es de guardar_figura).
#  - Defaults de PANTALLA (fuentes ~10-14 pt, figsize chico), no los de poster
#    del doc (font_size=137.5, figsize 60x60); `escala_fuente` multiplica los
#    tamanos base para poder subirlos a tamano paper.
#  - Sin el auto-sizing set_size (UnboundLocalError si el valor formateado mas
#    largo tiene <= 3 caracteres); figsize entra por parametro.
#  - Plot3D: UNA sola vista (parametro `vista`), no el loop de 5 del doc.
# ─────────────────────────────────────────────────────────────────────────────
def figura_frente_2d(puntos: np.ndarray, *, titulo: str | None = None,
                     etiquetas: tuple[str, str] = ("$f_1$", "$f_2$"),
                     figsize: tuple[float, float] = (6, 6),
                     escala_fuente: float = 1.0) -> "plt.Figure":
    """Scatter 2D (columnas 0 y 1) con el estilo del doc a tamano de pantalla."""
    P = np.asarray(puntos, dtype=float)
    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(P[:, 0], P[:, 1], s=18 * escala_fuente, alpha=1,
               color="darkblue", zorder=2)
    ax.minorticks_on()
    ax.grid(which="major", linestyle="--", linewidth=0.8, color="black", zorder=0)
    ax.grid(which="minor", linestyle=":", linewidth=0.5, color="gray", zorder=1)
    ax.tick_params(axis="both", labelsize=10 * escala_fuente)
    ax.set_xlabel(etiquetas[0], fontsize=12 * escala_fuente)
    ax.set_ylabel(etiquetas[1], fontsize=12 * escala_fuente)
    if titulo:
        fig.suptitle(titulo, fontsize=13 * escala_fuente, fontweight="bold",
                     family="monospace", y=0.97)
    fig.tight_layout()
    return fig


def figura_frente_3d(puntos: np.ndarray, *, titulo: str | None = None,
                     etiquetas: tuple[str, str, str] = ("$f_1$", "$f_2$", "$f_3$"),
                     figsize: tuple[float, float] = (7, 7),
                     vista: tuple[float, float] = (30, 45),
                     escala_fuente: float = 1.0) -> "plt.Figure":
    """Scatter 3D (columnas 0, 1 y 2), una sola vista (elev, azim)."""
    P = np.asarray(puntos, dtype=float)
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(projection="3d")
    ax.scatter(P[:, 0], P[:, 1], P[:, 2], s=12 * escala_fuente, alpha=1,
               color="darkblue")
    ax.grid(which="major", linestyle="--", linewidth=0.8, color="black", zorder=0)
    ax.tick_params(axis="both", which="major", labelsize=9 * escala_fuente, pad=2)
    ax.set_xlabel(etiquetas[0], fontsize=12 * escala_fuente, labelpad=8)
    ax.set_ylabel(etiquetas[1], fontsize=12 * escala_fuente, labelpad=8)
    ax.zaxis.set_rotate_label(False)          # como el doc: f3 horizontal
    ax.set_zlabel(etiquetas[2], fontsize=12 * escala_fuente, rotation=0, labelpad=8)
    ax.view_init(*vista)
    if titulo:
        fig.suptitle(titulo, fontsize=13 * escala_fuente, fontweight="bold",
                     family="monospace", y=0.97)
    return fig


def figura_frente(puntos: np.ndarray, m: int | None = None, **kw) -> "plt.Figure":
    """
    Dispatcher por dimension: m==2 -> figura_frente_2d, m==3 -> figura_frente_3d,
    m>=4 -> NotImplementedError. Si m es None se infiere de las columnas.
    Reenvia **kw a la funcion concreta (titulo, etiquetas, figsize, ...).
    """
    P = np.asarray(puntos, dtype=float)
    if m is None:
        m = P.shape[1]
    if m == 2:
        return figura_frente_2d(P, **kw)
    if m == 3:
        return figura_frente_3d(P, **kw)
    raise NotImplementedError("visualización m>3 pendiente")


def guardar_figura(fig: "plt.Figure", formato_ui: str) -> bytes | None:
    """
    Exporta la figura a bytes. PNG/SVG/EPS son reales aqui.
    TikZ/.tex devuelve None (FUTURO: requiere tikzplotlib o el backend pgf).
    """
    mapa = {"PNG (prioritario)": "png", "PNG": "png", "SVG": "svg", "EPS": "eps"}
    fmt = mapa.get(formato_ui)
    if fmt is None:
        return None
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=150, bbox_inches="tight")
    return buf.getvalue()


def cerrar(fig: "plt.Figure") -> None:
    """Libera la figura (evita acumular memoria entre reruns)."""
    plt.close(fig)
