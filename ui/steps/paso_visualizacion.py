# -*- coding: utf-8 -*-
"""
Paso 4 · VISUALIZACION: graficar el frente asociado a la mediana del indicador
(o el elegido), con matplotlib (motor unico), y descargar la figura.
"""
from __future__ import annotations

import streamlit as st

from domain import figures, indicators
from .. import components, state

# PNG por defecto (prioritario); el usuario elige otro formato si quiere.
FORMATOS = ["PNG", "SVG", "EPS", "TikZ (.tex)"]


def render() -> None:
    st.subheader("Paso 4 · Visualizacion de frentes")
    st.caption("Por defecto se grafica la corrida asociada a la MEDIANA del "
               "indicador elegido (tambien puedes elegir otra).")

    nombres = {m.id: m.nombre for m in indicators.CATALOGO.values()}
    s1, s2, s3 = st.columns(3)
    s1.text_input("MOEA", key="viz_moea", placeholder="(del paso Datos)")
    s2.text_input("MOP", key="viz_mop", placeholder="(del paso Datos)")
    s3.selectbox("Indicador (mediana)", list(indicators.CATALOGO),
                 format_func=lambda i: nombres[i], key="viz_ind")

    o1, o2 = st.columns(2)
    metodo = o1.selectbox("Metodo de visualizacion", figures.METODOS, key="viz_met")
    o2.selectbox("Corrida", ["Mediana (segun indicador)", "Mejor",
                             "Corrida especifica..."], key="viz_run")

    st.divider()
    st.markdown("#### Figura")
    components.placeholder(
        f"grafica del frente · {metodo}",
        "se dibujara el PFA (y, si aplica, el frente de referencia) con matplotlib.",
    )
    st.markdown("##### Descargar figura")
    components.descargas("figura", FORMATOS)

    st.divider()
    if st.button("Anterior", width="stretch"):
        state.ir_a(2)
        st.rerun()
