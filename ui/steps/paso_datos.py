# -*- coding: utf-8 -*-
"""
Paso 1 · DATOS: cargar y organizar los PFA (MOEA -> MOP -> corridas) y los
frentes de referencia. Al confirmar, desbloquea el paso de Indicadores.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from domain.model import CORRIDAS_ESTANDAR, CORRIDAS_MINIMAS
from .. import components, state


def render() -> None:
    st.subheader("Paso 1 · Carga y organizacion de datos")
    st.caption(
        "Se cargan las aproximaciones al frente de Pareto (PFA). La app NO "
        "ejecuta MOEAs: solo evalua y visualiza resultados ya generados."
    )
    st.info(
        "Modelo: cada MOEA se prueba en varios MOP; por cada MOP hay varias "
        "CORRIDAS; cada corrida produce un PFA. Unidad de carga = 1 CSV por PFA "
        "= N filas (puntos) x m columnas (objetivos)."
    )

    col_izq, col_der = st.columns([1.1, 1], gap="large")

    with col_izq:
        st.markdown("#### 1) Subir archivos de PFA")
        # FUTURO: cada archivo se parsea con la config de la barra lateral y se
        # valida (nro de columnas = m) en la capa de datos (csv_io.leer_pfa).
        st.file_uploader(
            "Arrastra uno o varios CSV con los PFA",
            type=["csv", "txt", "dat", "pf", "pof"],
            accept_multiple_files=True, key="up_pfa",
            help="Cada archivo = un PFA (puntos de una corrida de un MOEA).",
        )

        st.markdown("#### 2) Asociar cada PFA a su MOEA / MOP / corrida")
        st.caption("Mapeo: una linea por archivo -> (MOEA, MOP, corrida). "
                   "FUTURO: se autocompleta desde el nombre del archivo.")
        df_map = pd.DataFrame(columns=["archivo", "MOEA", "MOP", "m", "corrida"])
        st.data_editor(
            df_map, num_rows="dynamic", width="stretch", key="map_pfa",
            column_config={
                "m": st.column_config.NumberColumn(min_value=2, step=1),
                "corrida": st.column_config.NumberColumn(min_value=1, step=1),
            },
        )
        st.caption(
            f"Estandar de literatura: {CORRIDAS_ESTANDAR} corridas por par "
            f"(MOEA, MOP). FUTURO: aviso si n < {CORRIDAS_MINIMAS}."
        )

    with col_der:
        st.markdown("#### Vista previa de un PFA")
        components.placeholder(
            "los puntos del PFA seleccionado",
            "N filas (puntos) x m columnas (objetivos), tal como se leen del CSV.",
        )

        st.markdown("#### Frentes de referencia")
        st.caption("Necesarios para indicadores basados en distancia "
                   "(IGD, IGD+, R2, Delta p, Epsilon+).")
        st.file_uploader("Subir frente(s) de referencia",
                         type=["csv", "txt", "dat", "pf"],
                         accept_multiple_files=True, key="up_ref")
        df_ref = pd.DataFrame(columns=["MOP", "m", "archivo_referencia"])
        st.data_editor(df_ref, num_rows="dynamic", width="stretch",
                       hide_index=True, key="map_ref")

    st.divider()
    # ── Gating: confirmar para desbloquear el siguiente paso ───────────────────
    if st.button("Confirmar carga y continuar", type="primary", width="stretch"):
        state.completar(0)
        state.ir_a(1)
        st.rerun()
