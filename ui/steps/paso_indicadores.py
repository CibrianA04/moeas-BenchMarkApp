# -*- coding: utf-8 -*-
"""
Paso 2 · INDICADORES: elegir indicadores y preprocesamiento. Al evaluar,
desbloquea el paso de Resultados.
"""
from __future__ import annotations

import streamlit as st

from domain import indicators
from .. import state

# Texto para el atributo de Pareto-compliance (primera clase).
_COMP = {
    "strict": "STRICT Pareto-compliant",
    "weak": "WEAK Pareto-compliant",
    "no": "NO Pareto-compliant",
}


def render() -> None:
    st.subheader("Paso 2 · Indicadores de calidad")
    st.caption("Cada PFA pasara por cada indicador elegido para producir los "
               "valores que luego se resumen por (MOEA, MOP).")

    todos = list(indicators.CATALOGO.values())
    nombre_por_id = {m.id: m.nombre for m in todos}

    st.markdown("#### Indicadores a evaluar")
    seleccion = st.multiselect(
        "Indicadores", options=[m.id for m in todos],
        default=[m.id for m in todos if m.grupo == "principal"][:4],
        format_func=lambda i: nombre_por_id[i],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("#### Parametros por indicador")
    if not seleccion:
        st.warning("Selecciona al menos un indicador.")
    for ind_id in seleccion:
        meta = indicators.CATALOGO[ind_id]
        with st.expander(meta.nombre, expanded=False):
            st.caption(meta.descripcion)
            if ind_id == "HV":
                st.caption("FUTURO: calculo via pymoo (interfaz lista para "
                           "binario en C).")
                modo = st.radio("Punto de referencia",
                                ["Automatico (nadir)", "1.1 x nadir", "Manual"],
                                horizontal=True, key=f"hv_{ind_id}")
                if modo == "Manual":
                    st.text_input("Vector de referencia", value="1.1, 1.1, 1.1",
                                  key=f"hvvec_{ind_id}")
            elif ind_id == "Eps+":
                st.radio("Variante", ["Aditivo", "Multiplicativo"],
                         horizontal=True, key=f"eps_{ind_id}")
            elif ind_id == "Riesz":
                st.number_input("Parametro s (0 = estimar)", value=0.0, step=0.5,
                                key=f"s_{ind_id}")
            elif ind_id == "SPD":
                st.number_input("Parametro theta", value=10.0, step=1.0,
                                key=f"theta_{ind_id}")
            if meta.requiere_ref:
                st.caption("Requiere frente de referencia (paso Datos).")
            st.caption(_COMP[meta.compliance])
            st.caption("Sentido: " + ("mayor mejor (max)." if meta.sentido == "max"
                                      else "menor mejor (min)."))

    st.divider()
    c_atras, c_eval = st.columns([1, 2])
    if c_atras.button("Anterior", width="stretch"):
        state.ir_a(0)
        st.rerun()
    if c_eval.button("Evaluar indicadores", type="primary", width="stretch",
                     disabled=not seleccion):
        # FUTURO: recorrer (MOEA, MOP, corrida, PFA) y calcular cada indicador.
        st.session_state[state.K_INDS] = seleccion
        state.completar(1)
        state.ir_a(2)
        st.rerun()
