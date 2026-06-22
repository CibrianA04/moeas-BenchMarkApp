# -*- coding: utf-8 -*-
"""
Barra lateral: configuracion global del proyecto, lectura de CSV y navegacion
entre pasos (con indicadores de estado y gating).
"""
from __future__ import annotations

import streamlit as st

from domain import services
from . import state


def render() -> None:
    with st.sidebar:
        st.markdown("## BenchMark-MOEAs")
        st.caption("Maqueta de interfaz · Estancia Delfin · CICESE")
        st.divider()

        # ── Proyecto (persistencia futura en SQLite) ───────────────────────────
        st.markdown("### Proyecto")
        st.text_input("Nombre del proyecto", key=state.K_PROY)
        c1, c2, c3 = st.columns(3)
        if c1.button("Nuevo", width="stretch"):
            # FUTURO: limpiar el estado y empezar un proyecto vacio.
            st.toast("FUTURO: nuevo proyecto.")
        if c2.button("Cargar", width="stretch"):
            st.toast(services.cargar_proyecto())   # devuelve mensaje FUTURO
        if c3.button("Guardar", width="stretch"):
            st.toast(services.guardar_proyecto(None))
        st.caption("FUTURO: cargar/guardar el proyecto completo en SQLite.")

        st.divider()

        # ── Lectura de CSV (detalle plegado: no estorba la demo de flujo) ──────
        with st.expander("Lectura de CSV (avanzado)"):
            st.caption("Como interpretar los archivos de PFA.")
            sep = st.selectbox(
                "Separador de columnas",
                ["Coma  ( , )", "Punto y coma  ( ; )", "Tabulador  ( \\t )",
                 "Espacio", "Personalizado..."],
                key=state.K_SEP,
                help="Caracter que separa los objetivos en cada fila del CSV.",
            )
            if sep == "Personalizado...":
                st.text_input("Separador personalizado", value="|", max_chars=3,
                              key="csv_sep_custom")
            st.selectbox("Separador decimal", ["Punto  ( . )", "Coma  ( , )"],
                         key=state.K_DEC)

        st.divider()

        # ── Progreso / navegacion con gating ───────────────────────────────────
        st.markdown("### Pasos")
        actual = state.paso_actual()
        for i, nombre in enumerate(state.PASOS):
            if state.esta_completo(i):
                etiqueta_estado = "hecho"
            elif i == actual:
                etiqueta_estado = "actual"
            elif state.puede_ir_a(i):
                etiqueta_estado = "disponible"
            else:
                etiqueta_estado = "bloqueado"
            col_txt, col_btn = st.columns([3, 1])
            col_txt.write(f"{i + 1}. {nombre}  ({etiqueta_estado})")
            # Boton 'Ir' habilitado solo si el paso esta desbloqueado.
            if col_btn.button("Ir", key=f"ir_{i}",
                              disabled=not state.puede_ir_a(i),
                              width="stretch"):
                state.ir_a(i)
                st.rerun()
        st.caption("Cada paso se desbloquea al completar el anterior.")

        st.divider()
        st.caption("v0.2 · maqueta en capas (sin logica)")
