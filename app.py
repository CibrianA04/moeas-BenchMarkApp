# -*- coding: utf-8 -*-
"""
================================================================================
 BenchMark-MOEAs  ·  MAQUETA DE INTERFAZ (solo diseno, SIN logica)
================================================================================
Estancia Verano Delfin · CICESE
App para EVALUAR y VISUALIZAR aproximaciones al frente de Pareto (PFA) de MOEAs.

Punto de entrada DELGADO: solo configura la pagina, inicializa el estado, dibuja
la barra lateral y despacha el paso actual. Toda la UI vive en ui/, la logica en
domain/ y la E/S en data/.

Arquitectura (dependencia en un solo sentido, REGLA DURA):
    ui (Streamlit)  ->  domain (logica, headless)  ->  data (persistencia, I/O)
    Nada por debajo de 'ui' importa Streamlit. st.session_state = unica fuente
    de verdad. Step gating: cada paso se desbloquea al completar el anterior.

Ejecutar:   streamlit run app.py
================================================================================
"""
import streamlit as st

from ui import components, sidebar, state
from ui.steps import (paso_datos, paso_indicadores, paso_resultados,
                      paso_visualizacion)

# set_page_config debe ser la PRIMERA llamada de Streamlit.
st.set_page_config(
    page_title="BenchMark-MOEAs (maqueta)",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Funcion render() de cada paso, en el orden del flujo (indexada por state.paso).
RENDER_PASOS = [
    paso_datos.render,
    paso_indicadores.render,
    paso_resultados.render,
    paso_visualizacion.render,
]


def main() -> None:
    state.init_estado()          # session_state como unica fuente de verdad
    sidebar.render()             # configuracion global + navegacion con gating

    st.title("Benchmarking de MOEAs — maqueta de interfaz")
    st.caption("Demo del FLUJO de la aplicacion (sin logica todavia). "
               "Todos los pasos estan desbloqueados para poder recorrerlos.")

    # Flujo siempre visible: en que paso estamos y cuales se completaron.
    components.stepper()

    st.divider()

    # Despacha el paso actual (en la maqueta puedes navegar libremente).
    i = max(0, min(state.paso_actual(), len(RENDER_PASOS) - 1))
    RENDER_PASOS[i]()


main()
