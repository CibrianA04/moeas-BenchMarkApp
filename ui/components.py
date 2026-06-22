# -*- coding: utf-8 -*-
"""
Componentes de presentacion reutilizables (maqueta).

  - stepper():   muestra los 4 pasos, resaltando el actual y los completados.
  - placeholder(): un hueco claro "aqui ira X" (SIN datos falsos).
  - descargas():  selector de formato + boton de descarga (PNG/CSV por defecto).
"""
from __future__ import annotations

import streamlit as st

from . import state


def stepper() -> None:
    """Dibuja el flujo de los 4 pasos: actual en negrita, completados con [x]."""
    actual = state.paso_actual()
    partes = []
    for i, nombre in enumerate(state.PASOS):
        marca = "[x]" if state.esta_completo(i) else f"{i + 1}."
        etiqueta = f"{marca} {nombre}"
        partes.append(f"**{etiqueta}**" if i == actual else etiqueta)
    st.markdown("  ->  ".join(partes))


def placeholder(titulo: str, descripcion: str = "") -> None:
    """
    Hueco de maqueta: indica QUE ira aqui (sin inventar datos). Sustituye a
    tablas/figuras mientras no hay datos reales cargados.
    """
    with st.container(border=True):
        st.markdown(f"**Aqui ira:** {titulo}")
        if descripcion:
            st.caption(descripcion)


def descargas(clave: str, formatos: list[str]) -> None:
    """
    Selector de formato + boton de descarga.

    El PRIMER formato de la lista es el que sale por DEFECTO (p. ej. PNG en
    figuras, CSV en tablas); el usuario puede elegir cualquier otro. En la
    maqueta el boton esta deshabilitado (aun no hay datos que exportar).
    """
    c1, c2 = st.columns([1, 2])
    c1.selectbox("Formato", formatos, key=f"fmt_{clave}")
    c2.button("Descargar", key=f"dl_{clave}", disabled=True, width="stretch",
              help="Se habilitara cuando haya datos para exportar.")
