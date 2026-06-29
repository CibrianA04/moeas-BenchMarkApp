# -*- coding: utf-8 -*-
"""
Paso 1 · DATOS: cargar y organizar los PFA reales. El usuario sube un .zip con
carpetas por MOEA (flujo principal) o .pof sueltos (pruebas rapidas). La UI lee
los bytes y se los pasa al dominio (services); 'data' nunca ve streamlit.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from domain import services
from domain.model import CORRIDAS_ESTANDAR, CORRIDAS_MINIMAS
from .. import components, state


def _procesar_subida(archivos) -> tuple[list, list]:
    """Lee los bytes de cada archivo subido y delega la ingesta en el dominio."""
    pfas, errores, sueltos = [], [], []
    for f in archivos:
        datos = f.getvalue()                      # bytes (la capa data no ve streamlit)
        if f.name.lower().endswith(".zip"):
            p, e = services.cargar_zip(datos)     # flujo principal
            pfas += p
            errores += e
        else:
            sueltos.append((f.name, datos))       # .pof suelto
    if sueltos:
        p, e = services.cargar_pofs(sueltos)
        pfas += p
        errores += e
    return pfas, errores


def render() -> None:
    st.subheader("Paso 1 · Carga y organizacion de datos")
    st.caption(
        "Se cargan las aproximaciones al frente de Pareto (PFA) reales. La app NO "
        "ejecuta MOEAs: solo evalua y visualiza resultados ya generados."
    )

    col_izq, col_der = st.columns([1.1, 1], gap="large")

    with col_izq:
        st.markdown("#### 1) Subir datos")
        archivos = st.file_uploader(
            "Arrastra un .zip (carpetas por MOEA) o varios .pof sueltos",
            type=["zip", "pof", "csv", "txt", "dat", "pf"],
            accept_multiple_files=True, key="up_pfa",
            help="Flujo principal: un .zip con una carpeta por MOEA y los .pof "
                 "dentro. Tambien aceptamos .pof sueltos para pruebas.",
        ) or []

        # Procesa SOLO cuando cambia el conjunto de archivos (evita reprocesar).
        firma = tuple(sorted((f.name, f.size) for f in archivos))
        if firma != st.session_state.get(state.K_FIRMA):
            with st.spinner("Leyendo y validando archivos..."):
                pfas, errores = _procesar_subida(archivos)
            st.session_state[state.K_PFAS] = pfas
            st.session_state[state.K_ERR] = errores
            st.session_state[state.K_FIRMA] = firma

        pfas = st.session_state.get(state.K_PFAS, [])
        errores = st.session_state.get(state.K_ERR, [])

        # Resumen: X cargados, Y omitidos (motivo).
        if archivos:
            if pfas:
                st.success(f"{len(pfas)} PFA cargados"
                           + (f"  ·  {len(errores)} omitidos" if errores else ""))
            else:
                st.error("No se cargo ningun PFA valido.")
            if errores:
                with st.expander(f"Ver {len(errores)} archivo(s) omitido(s)"):
                    st.dataframe(
                        pd.DataFrame(errores, columns=["archivo", "motivo"]),
                        width="stretch", hide_index=True,
                    )

        st.markdown("#### 2) Mapeo (MOEA / MOP / m / n / corrida)")
        st.caption("Autocompletado desde el nombre de cada archivo "
                   "({MOEA}_{MOP}_{m}D_N{N}_R{run}.pof).")
        df_map = (services.mapeo_desde_pfas(pfas) if pfas
                  else pd.DataFrame(columns=services.COLS_MAPEO))
        st.data_editor(
            df_map, num_rows="dynamic", width="stretch", hide_index=True,
            key="map_pfa",
            column_config={
                "m": st.column_config.NumberColumn(min_value=2, step=1),
                "n": st.column_config.NumberColumn(min_value=1, step=1),
                "corrida": st.column_config.NumberColumn(min_value=0, step=1),
            },
        )
        st.caption(
            f"Estandar de literatura: {CORRIDAS_ESTANDAR} corridas por par "
            f"(MOEA, MOP). FUTURO: aviso si n < {CORRIDAS_MINIMAS}."
        )

    with col_der:
        st.markdown("#### Vista previa de un PFA")
        if pfas:
            opciones = [p.archivo for p in pfas]
            elegido = st.selectbox("Archivo", opciones, key="preview_sel")
            pfa = next(p for p in pfas if p.archivo == elegido)
            st.caption(f"{pfa.moea} · {pfa.mop} · m={pfa.m} · N={pfa.n} · "
                       f"corrida {pfa.corrida}  ({pfa.puntos.shape[0]} puntos)")
            st.dataframe(services.preview_de_pfa(pfa, 10),
                         width="stretch", hide_index=True)
        else:
            components.placeholder(
                "los puntos del PFA seleccionado",
                "Sube datos para ver las primeras filas (N puntos x m objetivos).",
            )

        st.markdown("#### Frentes de referencia")
        st.caption("Necesarios para indicadores basados en distancia "
                   "(IGD, IGD+, R2, Delta p, Epsilon+).")
        st.file_uploader("Subir frente(s) de referencia",
                         type=["csv", "txt", "dat", "pf", "pof"],
                         accept_multiple_files=True, key="up_ref")
        df_ref = pd.DataFrame(columns=["MOP", "m", "archivo_referencia"])
        st.data_editor(df_ref, num_rows="dynamic", width="stretch",
                       hide_index=True, key="map_ref")

    st.divider()
    # ── Avance del flujo ───────────────────────────────────────────────────────
    if st.button("Confirmar carga y continuar", type="primary", width="stretch"):
        state.completar(0)
        state.ir_a(1)
        st.rerun()
