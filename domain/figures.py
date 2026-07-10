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

# Metodos de visualizacion disponibles (extensible: agregar = una entrada + su
# funcion; para m>3 tambien una entrada en _FIGURAS_M4, abajo).
METODOS = [
    "Dispersion 2D",
    "Dispersion 3D",
    "Coordenadas paralelas",
    "Radar",
    "Burbuja",
    "Heatmap",
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


# ─────────────────────────────────────────────────────────────────────────────
#  Port de las visualizaciones m>3 de MOEA-visualization-main (parallel_coord /
#  radar / bubble / heatmap), HEADLESS y con las mismas diferencias deliberadas
#  que Plot2D/Plot3D: reciben ndarray (n, m) ya parseado, devuelven Figure sin
#  savefig/show, defaults de PANTALLA con `escala_fuente`, y una sola vista.
#  Ademas normalizan cada columna a [0, 1] (objetivos con escalas distintas no
#  son comparables en un mismo eje); el heatmap del doc ya normalizaba asi.
# ─────────────────────────────────────────────────────────────────────────────
def _normalizar_01(P: np.ndarray) -> np.ndarray:
    """Normaliza cada columna a [0,1]; una columna constante queda en 0."""
    mn, mx = P.min(axis=0), P.max(axis=0)
    rango = np.where(mx > mn, mx - mn, 1.0)
    return (P - mn) / rango


def _etiquetas_f(m: int, etiquetas=None) -> list[str]:
    """Etiquetas $f_1..f_m$ por default (mismo formato que los scripts del doc)."""
    return list(etiquetas) if etiquetas else [f"$f_{{{j + 1}}}$" for j in range(m)]


def _titular(fig: "plt.Figure", titulo: str | None, escala_fuente: float) -> None:
    """Titulo con el formato del doc (bold, monospace, y=0.97)."""
    if titulo:
        fig.suptitle(titulo, fontsize=13 * escala_fuente, fontweight="bold",
                     family="monospace", y=0.97)


def figura_parallel(puntos: np.ndarray, *, titulo: str | None = None,
                    etiquetas: list[str] | None = None,
                    figsize: tuple[float, float] = (7, 5),
                    escala_fuente: float = 1.0) -> "plt.Figure":
    """Coordenadas paralelas: un eje vertical por objetivo, una linea por
    solucion (color darkblue y grid como el parallel_coord del doc)."""
    P = np.asarray(puntos, dtype=float)
    n, m = P.shape
    etiquetas = _etiquetas_f(m, etiquetas)
    P = _normalizar_01(P)
    fig, ax = plt.subplots(figsize=figsize)
    xs = np.arange(1, m + 1)
    for i in range(n):
        ax.plot(xs, P[i], color="darkblue", lw=0.8 * escala_fuente,
                alpha=0.6, zorder=2)
    ax.set_xticks(xs)
    ax.set_xticklabels(etiquetas, fontsize=12 * escala_fuente)
    ax.set_xlim(1, m)
    ax.set_ylim(-0.02, 1.02)
    ax.minorticks_on()
    ax.grid(which="major", linestyle="--", linewidth=0.8, color="black", zorder=0)
    ax.grid(which="minor", linestyle=":", linewidth=0.5, color="gray", zorder=1)
    ax.tick_params(axis="y", labelsize=10 * escala_fuente)
    ax.set_xlabel("Objetivos", fontsize=12 * escala_fuente)
    ax.set_ylabel("Valor normalizado", fontsize=12 * escala_fuente)
    _titular(fig, titulo, escala_fuente)
    fig.tight_layout()
    return fig


def figura_radar(puntos: np.ndarray, *, titulo: str | None = None,
                 etiquetas: list[str] | None = None,
                 figsize: tuple[float, float] = (6, 6),
                 escala_fuente: float = 1.0) -> "plt.Figure":
    """Radar (arana): un angulo por objetivo, un poligono cerrado por solucion
    (color darkred y grid gris como el radar del doc)."""
    P = np.asarray(puntos, dtype=float)
    n, m = P.shape
    etiquetas = _etiquetas_f(m, etiquetas)
    P = _normalizar_01(P)
    angulos = np.linspace(0, 2 * np.pi, m, endpoint=False)
    cerrados = np.concatenate([angulos, angulos[:1]])  # cierra el circulo
    fig, ax = plt.subplots(figsize=figsize, subplot_kw={"polar": True})
    for i in range(n):
        ax.plot(cerrados, np.concatenate([P[i], P[i, :1]]), color="darkred",
                lw=0.8 * escala_fuente, alpha=0.6, zorder=2)
    ax.grid(which="major", linewidth=0.8, color="gray", zorder=0)
    ax.set_xticks(angulos)
    ax.set_xticklabels(etiquetas, fontsize=12 * escala_fuente)
    ax.set_ylim(0, 1.02)
    ax.set_rlabel_position(0)                # radios sobre el eje 0, como el doc
    ax.tick_params(axis="y", labelsize=8 * escala_fuente)
    _titular(fig, titulo, escala_fuente)
    fig.tight_layout()
    return fig


def figura_bubble(puntos: np.ndarray, *, titulo: str | None = None,
                  etiquetas: tuple[str, str, str] = ("$f_1$", "$f_2$", "$f_3$"),
                  figsize: tuple[float, float] = (7, 7),
                  vista: tuple[float, float] = (30, 45),
                  escala_fuente: float = 1.0) -> "plt.Figure":
    """
    Burbuja 3D: f1,f2,f3 en los ejes; f4 (si m>=4) en el COLOR (colorbar $f_4$
    con el cmap del doc) y f5 (si m>=5) en el TAMANO de la burbuja. Con m==3
    degrada a un scatter 3D simple. Requiere m >= 3.
    """
    P = np.asarray(puntos, dtype=float)
    n, m = P.shape
    if m < 3:
        raise ValueError(f"figura_bubble requiere m >= 3 (recibio m={m}).")
    if m >= 5:                               # f5 normalizada -> tamano de burbuja
        f5 = _normalizar_01(P[:, 4:5])[:, 0]
        tam = (15 + 85 * f5) * escala_fuente
    else:
        tam = 12 * escala_fuente
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(projection="3d")
    if m >= 4:
        disp = ax.scatter(P[:, 0], P[:, 1], P[:, 2], s=tam, alpha=1,
                          c=P[:, 3], cmap="gist_rainbow_r")
        barra = fig.colorbar(disp, location="right", pad=0.1, shrink=0.7)
        barra.ax.tick_params(labelsize=9 * escala_fuente)
        barra.set_label("$f_4$", rotation=0, labelpad=10,
                        fontsize=12 * escala_fuente)
    else:
        ax.scatter(P[:, 0], P[:, 1], P[:, 2], s=tam, alpha=1, color="darkblue")
    ax.grid(which="major", linestyle="--", linewidth=0.8, color="black", zorder=0)
    ax.tick_params(axis="both", which="major", labelsize=9 * escala_fuente, pad=2)
    ax.set_xlabel(etiquetas[0], fontsize=12 * escala_fuente, labelpad=8)
    ax.set_ylabel(etiquetas[1], fontsize=12 * escala_fuente, labelpad=8)
    ax.zaxis.set_rotate_label(False)         # como el doc: f3 horizontal
    ax.set_zlabel(etiquetas[2], fontsize=12 * escala_fuente, rotation=0, labelpad=8)
    ax.view_init(*vista)
    _titular(fig, titulo, escala_fuente)
    return fig


def figura_heatmap(puntos: np.ndarray, *, titulo: str | None = None,
                   etiquetas: list[str] | None = None,
                   figsize: tuple[float, float] = (6, 5),
                   escala_fuente: float = 1.0) -> "plt.Figure":
    """Heatmap: matriz (filas=soluciones, columnas=objetivos) normalizada por
    columna, cmap Blues + colorbar, xticks $f_i$ y sin yticks (como el doc)."""
    P = np.asarray(puntos, dtype=float)
    m = P.shape[1]
    etiquetas = _etiquetas_f(m, etiquetas)
    P = _normalizar_01(P)
    fig, ax = plt.subplots(figsize=figsize)
    mapa = ax.matshow(P, cmap="Blues", norm=plt.Normalize(vmin=0, vmax=1))
    ax.set_xticks(np.arange(m))
    ax.set_xticklabels(etiquetas, rotation=45, ha="right",
                       fontsize=12 * escala_fuente)
    ax.set_yticks([])
    barra = fig.colorbar(mapa)
    barra.ax.tick_params(labelsize=9 * escala_fuente)
    ax.set_aspect("auto")                    # llena el rectangulo de datos
    _titular(fig, titulo, escala_fuente)
    return fig


# Metodos para m>3 (nombre visible en la UI -> constructor de la figura).
_FIGURAS_M4 = {
    "Coordenadas paralelas": figura_parallel,
    "Radar": figura_radar,
    "Burbuja": figura_bubble,
    "Heatmap": figura_heatmap,
}
METODOS_M4 = list(_FIGURAS_M4)


def figura_frente(puntos: np.ndarray, m: int | None = None,
                  metodo: str = "Coordenadas paralelas", **kw) -> "plt.Figure":
    """
    Dispatcher por dimension: m==2 -> figura_frente_2d, m==3 -> figura_frente_3d
    (en ambos `metodo` se ignora), m>3 -> la figura de `metodo` (una de
    METODOS_M4; default coordenadas paralelas). Si m es None se infiere de las
    columnas. Reenvia **kw a la funcion concreta (titulo, etiquetas, figsize, ...).
    """
    P = np.asarray(puntos, dtype=float)
    if m is None:
        m = P.shape[1]
    if m == 2:
        return figura_frente_2d(P, **kw)
    if m == 3:
        return figura_frente_3d(P, **kw)
    construir = _FIGURAS_M4.get(metodo)
    if construir is None:
        raise ValueError(f"Metodo desconocido para m>3: '{metodo}'. "
                         f"Opciones: {METODOS_M4}.")
    return construir(P, **kw)


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
