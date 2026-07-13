# -*- coding: utf-8 -*-
"""
================================================================================
 BenchMark-MOEAs  
================================================================================
App para EVALUAR y VISUALIZAR aproximaciones al frente de Pareto (PFA) de MOEAs.

Ejecutar:   py -m streamlit run app.py
================================================================================
"""
import streamlit as st

from ui import components, sidebar, state
from ui.steps import (paso_datos, paso_indicadores, paso_resultados,
                      paso_visualizacion)

st.set_page_config(
    page_title="BenchMark-MOEAs",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Funcion render() de cada paso, orden del flujo
RENDER_PASOS = [
    paso_datos.render,
    paso_indicadores.render,
    paso_resultados.render,
    paso_visualizacion.render,
]


def main() -> None:
    state.init_estado()          # session_state como unica fuente de verdad
    sidebar.render()             # configuracion global + navegacion con gating

    st.title("Benchmarking de MOEAs ")
    st.caption("Flujo: Datos -> Indicadores -> Resultados -> Visualizacion.")

    # Flujo siempre visible: en que paso estamos y cuales se completaron.
    components.stepper()

    st.divider()

    # Despacha el paso actual (indice acotado por si el estado trae un valor raro).
    i = max(0, min(state.paso_actual(), len(RENDER_PASOS) - 1))
    RENDER_PASOS[i]()


main()
