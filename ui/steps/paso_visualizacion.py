# -*- coding: utf-8 -*-
"""
Paso 4 · VISUALIZACION: graficar el frente de un PFA real con matplotlib (motor
unico). Se elige MOEA / MOP / corrida entre los datos cargados en el Paso 1 y se
dibuja con las funciones que YA existen (2D si m=2, 3D si m=3).
"""
from __future__ import annotations

import streamlit as st

from domain import figures
from .. import components, state

# PNG por defecto (prioritario); el usuario elige otro formato si quiere.
FORMATOS = ["PNG", "SVG", "EPS", "TikZ (.tex)"]


def render() -> None:
    st.subheader("Paso 4 · Visualizacion de frentes")

    pfas = st.session_state.get(state.K_PFAS, [])
    if not pfas:
        st.info("Primero carga datos en el **Paso 1 · Datos** "
                "(sube el .zip o .pof sueltos).")
        if st.button("Ir al Paso 1", width="stretch"):
            state.ir_a(0)
            st.rerun()
        return

    st.caption("Elige el PFA a graficar entre los datos cargados.")

    # Selectores encadenados, derivados de los PFA realmente cargados.
    s1, s2, s3 = st.columns(3)
    moeas = sorted({p.moea for p in pfas})
    moea = s1.selectbox("MOEA", moeas, key="viz_moea")
    mops = sorted({p.mop for p in pfas if p.moea == moea})
    mop = s2.selectbox("MOP", mops, key="viz_mop")
    candidatos = [p for p in pfas if p.moea == moea and p.mop == mop]
    corridas = sorted({p.corrida for p in candidatos})
    corrida = s3.selectbox("Corrida", corridas, key="viz_run")

    pfa = next(p for p in candidatos if p.corrida == corrida)

    st.divider()
    st.markdown("#### Figura")
    titulo = f"{pfa.moea} · {pfa.mop} · corrida {pfa.corrida}  (m={pfa.m}, N={pfa.n})"

    # El DOMINIO construye la figura (matplotlib headless); la UI solo la muestra.
    fig = None
    if pfa.m == 2:
        fig = figures.fig_scatter_2d(pfa.puntos, titulo=titulo)
    elif pfa.m == 3:
        fig = figures.fig_scatter_3d(pfa.puntos, titulo=titulo)
    else:
        st.info(f"m={pfa.m}: para m>3 se usaran coordenadas paralelas (futuro).")

    if fig is not None:
        st.pyplot(fig)
        figures.cerrar(fig)        # libera memoria entre reruns

    st.markdown("##### Descargar figura")
    components.descargas("figura", FORMATOS)

    st.divider()
    if st.button("Anterior", width="stretch"):
        state.ir_a(2)
        st.rerun()
