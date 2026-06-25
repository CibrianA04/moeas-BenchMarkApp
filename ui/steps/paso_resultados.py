# -*- coding: utf-8 -*-
"""
Paso 3 · RESULTADOS: tabla por indicador (mejor media resaltada), pruebas
estadisticas por escenario y exportacion (CSV / LaTeX).
"""
from __future__ import annotations

import streamlit as st

from domain import indicators, statistics
from .. import components, state


def render() -> None:
    st.subheader("Paso 3 · Resultados y tablas")
    st.caption("UNA tabla por indicador. La mejor media de cada "
               "fila se resaltara; debajo, pruebas estadisticas por escenario.")

    nombres = {m.id: m.nombre for m in indicators.CATALOGO.values()}
    # Por defecto, los indicadores elegidos en el paso anterior (o todos).
    elegidos = st.session_state.get(state.K_INDS) or list(indicators.CATALOGO)

    c1, c2 = st.columns([2, 1])
    ind_id = c1.selectbox("Indicador", elegidos, format_func=lambda i: nombres[i])
    meta = indicators.CATALOGO[ind_id]

    if meta.compliance == "no":
        st.warning("Indicador NO Pareto-compliant ")
    else:
        st.success(f"Pareto-compliant ({meta.compliance}) ")

    # ── Tabla (la construira domain/tables.py cuando haya datos) ───────────────
    components.placeholder(
        f"tabla del indicador {nombres[ind_id]}",
        "filas = (MOP, m) · columnas = MOEAs · celda = media (desv); la mejor "
        "media de cada fila se resaltara.",
    )
    st.markdown("##### Descargar tabla")
    components.descargas("tabla", ["CSV", "LaTeX (.tex)", "Markdown"])

    st.divider()

    # ── Pruebas estadisticas: el dominio decide la prueba segun el escenario ───
    st.markdown("#### Pruebas de desempeno")
    escenario = st.radio("Escenario",
                         ["pareado", "independiente", "multi"], horizontal=True,
                         format_func=lambda e: {"pareado": "Pareado (2 MOEAs)",
                                                "independiente": "Independiente (2)",
                                                "multi": "Multi-algoritmo (3+)"}[e])
    st.caption(f"Prueba recomendada para este escenario: "
               f"**{statistics.recomendar_prueba(escenario)}** "
               "(la decide `domain/statistics.py`).")
    components.placeholder(
        "matriz de comparacion por escenario",
        "simbolos + / - / = (mejor / peor / equivalente que la referencia). "
        "Multi-algoritmo -> Friedman + post-hoc + Critical Differences plot.",
    )

    st.markdown("##### Critical Differences plot (futuro)")
    st.caption("Ranking de MOEAs y grupos sin diferencia significativa.")
    components.descargas("cd_plot", ["PNG", "SVG", "EPS", "TikZ (.tex)"])

    # Visitar este paso lo marca como completado (avance del flujo).
    state.completar(2)
    st.divider()
    c_atras, c_sig = st.columns([1, 2])
    if c_atras.button("Anterior", width="stretch"):
        state.ir_a(1)
        st.rerun()
    if c_sig.button("Ir a Visualizacion", type="primary", width="stretch"):
        state.ir_a(3)
        st.rerun()
