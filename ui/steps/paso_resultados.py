# -*- coding: utf-8 -*-
"""
Paso 3 · RESULTADOS: tabla por indicador (mejor media resaltada), pruebas
estadisticas por escenario, CD plot y exportacion (CSV / LaTeX / Markdown).

Consume la salida del motor (`state.K_RES`/`state.K_OMIT`, producida en el Paso 2
por `domain.evaluacion.evaluar`) y la presenta con `domain.tables` /
`domain.statistics`. La app NO recalcula estadistica aqui: solo la muestra.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from domain import figures, indicators, statistics, tables
from domain.tables import tabla_display
from .. import components, state

# Estilo del resaltado de la mejor media (rank 1) de cada fila.
_RESALTE = "background-color: rgba(33, 150, 83, 0.35); font-weight: 700;"

# Formatos de descarga del CD plot (mismo mecanismo que las figuras del Paso 4).
_EXT_MIME = {
    "PNG": ("png", "image/png"),
    "SVG": ("svg", "image/svg+xml"),
    "EPS": ("eps", "application/postscript"),
    "TikZ (.tex)": ("tex", "application/x-tex"),
}


def _mostrar_tabla(est: pd.DataFrame, moeas: list[str]) -> None:
    """Dibuja la tabla plana con la mejor media de cada fila resaltada."""
    display, mask = tabla_display(est, moeas)
    estilos = pd.DataFrame(np.where(mask.to_numpy(), _RESALTE, ""),
                           index=display.index, columns=display.columns)
    styler = display.style.apply(lambda _: estilos, axis=None)
    st.dataframe(styler, width="stretch", hide_index=True)


def _mostrar_significancia(resultados: list[dict], ind_id: str,
                           filtro_n: int | None) -> None:
    """Evidencia +/-/= por escenario (Mann-Whitney hacia el ganador)."""
    sig = statistics.significancia(
        [r for r in resultados if r["indicador"] == ind_id])
    if filtro_n is not None and not sig.empty:
        sig = sig[sig["N"] == filtro_n]
    if sig.empty:
        st.caption("Sin comparaciones: se necesitan >= 2 MOEAs por escenario "
                   "(MOP, m, N).")
        return
    vista = sig.copy()
    vista.insert(0, "escenario",
                 vista["mop"] + " - m=" + vista["m"].astype(str)
                 + " - N=" + vista["N"].astype(str))
    vista = vista[["escenario", "ganador", "rival", "p_value", "significativo"]]
    st.dataframe(vista, width="stretch", hide_index=True)

    # Descarga de la tabla mostrada (mismas filas/columnas que `vista`).
    proyecto = st.session_state.get(state.K_PROY, "experimento")
    base = f"{proyecto}_{ind_id}_significancia"
    datos = {
        "CSV": (vista.to_csv(index=False).encode("utf-8"),
                f"{base}.csv", "text/csv"),
        "Markdown": (tables.df_a_markdown(vista).encode("utf-8"),
                     f"{base}.md", "text/markdown"),
        "LaTeX (.tex)": (vista.to_latex(index=False).encode("utf-8"),
                         f"{base}.tex", "text/plain"),
    }
    components.descargas("significancia", list(datos), datos_por_formato=datos)


def _mostrar_cd_plot(resultados: list[dict], ind_id: str, nombre: str,
                     filtro_n: int | None) -> None:
    """CD plot (Demsar): rangos promedio y grupos sin diferencia significativa,
    coherente con el indicador y el filtro de N en pantalla."""
    sub = [r for r in resultados if r["indicador"] == ind_id]
    if filtro_n is not None:
        sub = [r for r in sub if r["N"] == filtro_n]
    cd = statistics.critical_differences(sub).get(ind_id)
    if cd is None:
        st.markdown("##### Critical Differences plot")
        st.info("Sin CD plot: se necesitan >= 2 MOEAs evaluados en este "
                "indicador (con el filtro actual).")
        return
    st.markdown(
        "##### Critical Differences plot",
        help=f"Nemenyi con alpha=0.05 sobre {cd.N} escenario(s) y {cd.k} "
             "MOEAs; una barra une a los que NO difieren significativamente.",
    )

    # El DOMINIO construye la figura; aqui solo se muestra y se exporta.
    fig = figures.figura_critical_differences(cd, titulo=f"CD plot · {nombre}")
    st.pyplot(fig)

    proyecto = st.session_state.get(state.K_PROY, "experimento")
    datos = {}
    for etiqueta, (ext, mime) in _EXT_MIME.items():
        contenido = figures.guardar_figura(fig, etiqueta)
        if contenido is not None:
            datos[etiqueta] = (contenido, f"{proyecto}_{ind_id}_cd.{ext}", mime)
    figures.cerrar(fig)                               # tras exportar los bytes
    components.descargas("cd_plot", list(_EXT_MIME), datos_por_formato=datos)


def _mostrar_omitidos() -> None:
    """Expander con lo que el motor NO calculo (sin frente ref / corrida mala)."""
    omit = st.session_state.get(state.K_OMIT) or []
    if not omit:
        return
    with st.expander(f"No calculado: {len(omit)} aviso(s)", expanded=False):
        sin_ref = [o for o in omit if o.get("tipo") == "sin_referencia"]
        fallidas = [o for o in omit if o.get("tipo") == "corrida_fallida"]
        if sin_ref:
            st.markdown("**Escenarios sin frente de referencia** (se omiten sus "
                        "indicadores basados en distancia):")
            st.dataframe(pd.DataFrame(sin_ref), width="stretch", hide_index=True)
        if fallidas:
            st.markdown("**Corridas que fallaron al calcular un indicador:**")
            st.dataframe(pd.DataFrame(fallidas), width="stretch", hide_index=True)


def _botones_navegacion() -> None:
    st.divider()
    c_atras, c_sig = st.columns([1, 2])
    if c_atras.button("Anterior", width="stretch"):
        state.ir_a(1)
        st.rerun()
    if c_sig.button("Ir a Visualizacion", type="primary", width="stretch"):
        state.ir_a(3)
        st.rerun()


def render() -> None:
    st.subheader("Paso 3 · Resultados y tablas")
    st.caption("Una tabla por indicador; la mejor media se resalta.")

    # Visitar este paso lo marca como completado (avance del flujo).
    state.completar(2)

    resultados = st.session_state.get(state.K_RES, [])
    if not resultados:
        st.info("Aun no hay resultados. Ve al Paso 2 y pulsa "
                "'Evaluar indicadores'.")
        _botones_navegacion()
        return

    nombres = {m.id: m.nombre for m in indicators.CATALOGO.values()}
    # Indicadores realmente evaluados (o los elegidos como respaldo) y MOEAs.
    elegidos = st.session_state.get(state.K_INDS) or sorted(
        {r["indicador"] for r in resultados})
    moeas = sorted({r["moea"] for r in resultados})

    c1, c2 = st.columns([2, 1])
    ind_id = c1.selectbox("Indicador", elegidos, format_func=lambda i: nombres[i])
    ns = sorted({r["N"] for r in resultados if r["indicador"] == ind_id})
    sel_n = c2.selectbox("N (poblacion)", ["Todas", *ns])
    filtro_n = None if sel_n == "Todas" else int(sel_n)

    meta = indicators.CATALOGO[ind_id]
    if meta.compliance == "no":
        st.warning("Indicador NO Pareto-compliant.")
    else:
        st.success(f"Pareto-compliant ({meta.compliance}).")

    # ── Tabla real por indicador ───────────────────────────────────────────────
    est = tables.tabla_estructurada(resultados, ind_id, moeas=moeas,
                                    filtro_n=filtro_n)
    datos = None
    if est.empty:
        st.warning(f"No hay datos de {nombres[ind_id]} con este filtro. Puede que "
                   "el indicador no se calculara (p. ej. sin frente de referencia).")
    else:
        _mostrar_tabla(est, moeas)
        proyecto = st.session_state.get(state.K_PROY, "experimento")
        caption = f"Desempeno segun {nombres[ind_id]}"
        datos = {
            "CSV": (tables.a_csv_doc(est),
                    f"{proyecto}_{ind_id}.csv", "text/csv"),
            "LaTeX (.tex)": (
                tables.a_latex_doc(est, ind_id, caption,
                                   f"tab:{ind_id}").encode("utf-8"),
                f"{proyecto}_{ind_id}.tex", "text/plain"),
            "Markdown": (tables.a_markdown_doc(est),
                         f"{proyecto}_{ind_id}.md", "text/markdown"),
        }

    st.markdown("##### Descargar tabla")
    components.descargas("tabla", ["CSV", "LaTeX (.tex)", "Markdown"],
                         datos_por_formato=datos)

    st.divider()

    # ── Pruebas de desempeno: evidencia estadistica del indicador/filtro ───────
    st.markdown(
        "#### Pruebas de desempeno",
        help="Mann-Whitney U de una cola hacia el ganador, alpha=0.05, sin "
             "correccion multiple (mismo criterio que la marca # de la tabla).",
    )
    _mostrar_significancia(resultados, ind_id, filtro_n)

    _mostrar_omitidos()

    _mostrar_cd_plot(resultados, ind_id, nombres[ind_id], filtro_n)

    _botones_navegacion()

