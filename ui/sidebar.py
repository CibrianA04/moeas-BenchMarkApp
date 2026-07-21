# -*- coding: utf-8 -*-
"""
Barra lateral: configuracion global del proyecto, lectura de CSV y navegacion
entre pasos (con indicadores de estado y gating).
"""
from __future__ import annotations

import streamlit as st

from domain import services
from . import state
from .steps.paso_indicadores import _K_WIDGET_INDS

# Claves privadas de la sidebar en session_state.
_K_BYTES = "_proyecto_bytes"            # snapshot .sqlite listo para descargar
_K_PENDIENTE = "_proyecto_pendiente"    # estado cargado, por aplicar al estado
_K_FIRMA_PROY = "_firma_proyecto"       # firma del .sqlite ya procesado


def _snapshot_estado() -> dict:
    """Snapshot de SESION desde session_state: solo lo que exista segun el
    paso (PFAs, frentes, seleccion, resultados). Sin parametros de calculo."""
    ss = st.session_state
    return {
        "nombre": ss.get(state.K_PROY) or "proyecto",
        "paso": ss.get(state.K_PASO, 0),
        "completado": list(ss.get(state.K_COMP) or [False] * len(state.PASOS)),
        "separador": ss.get(state.K_SEP),
        "decimal": ss.get(state.K_DEC),
        "indicadores": list(ss.get(state.K_INDS) or []),
        "pfas": list(ss.get(state.K_PFAS) or []),
        "frentes_ref": dict(ss.get(state.K_FREJ) or {}),
        "resultados": list(ss.get(state.K_RES) or []),
        "omitidos": list(ss.get(state.K_OMIT) or []),
    }


def _aplicar_carga_pendiente() -> None:
    """Rehidrata session_state con un snapshot cargado. Corre al INICIO del
    render porque claves como K_PROY pertenecen a widgets y streamlit no
    permite pisarlas despues de instanciarlos en el mismo run."""
    estado = st.session_state.pop(_K_PENDIENTE, None)
    if estado is None:
        return
    ss = st.session_state
    ss[state.K_PROY] = estado.get("nombre") or "proyecto"
    if estado.get("separador"):
        ss[state.K_SEP] = estado["separador"]
    if estado.get("decimal"):
        ss[state.K_DEC] = estado["decimal"]
    ss[state.K_PFAS] = estado.get("pfas") or []
    ss[state.K_ERR] = []                      # los omitidos de carga no se guardan
    ss[state.K_FREJ] = estado.get("frentes_ref") or {}
    ss[state.K_REF_ERR] = []
    ss[state.K_INDS] = estado.get("indicadores") or []
    ss[state.K_RES] = estado.get("resultados") or []
    ss[state.K_OMIT] = estado.get("omitidos") or []
    ss.pop(_K_WIDGET_INDS, None)              # el multiselect se resiembra de K_INDS

    # Gating: el completado guardado manda con resultados cargados, Datos e
    # Indicadores cuentan como completos (asi Resultados queda alcanzable).
    comp = list(estado.get("completado") or [False] * len(state.PASOS))
    comp += [False] * (len(state.PASOS) - len(comp))   # por si viene corta
    if ss[state.K_RES]:
        comp[0] = comp[1] = True
    ss[state.K_COMP] = comp[:len(state.PASOS)]
    paso = int(estado.get("paso") or 0)
    paso = max(0, min(paso, len(state.PASOS) - 1))
    ss[state.K_PASO] = paso if all(ss[state.K_COMP][:paso]) else 0
    st.toast(f"Proyecto '{ss[state.K_PROY]}' cargado.")


def _controles_proyecto() -> None:
    """Guardar (snapshot -> descarga .sqlite) y Cargar (upload -> rehidratar)."""
    if st.button("Guardar proyecto", width="stretch",
                 help="Snapshot de la sesión actual (datos, selección y "
                      "resultados; sin parámetros de cálculo). Se entrega como "
                      "descarga porque el disco del servidor es efímero."):
        try:
            st.session_state[_K_BYTES] = services.proyecto_a_bytes(_snapshot_estado())
        except Exception as exc:  # noqa: BLE001 (guardar nunca tumba la app)
            st.session_state.pop(_K_BYTES, None)
            st.error(f"No se pudo preparar el guardado: {exc}")
    if st.session_state.get(_K_BYTES) is not None:
        nombre = st.session_state.get(state.K_PROY) or "proyecto"
        st.download_button("Descargar proyecto (.sqlite)",
                           data=st.session_state[_K_BYTES],
                           file_name=f"{nombre}.sqlite",
                           mime="application/x-sqlite3",
                           key="dl_proyecto", width="stretch")

    subida = st.file_uploader("Cargar proyecto (.sqlite)",
                              type=["sqlite", "db"], key="up_proyecto")
    if subida is not None:
        firma = (subida.name, subida.size)
        if st.session_state.get(_K_FIRMA_PROY) != firma:   # no re-cargar por rerun
            st.session_state[_K_FIRMA_PROY] = firma
            try:
                estado = services.cargar_proyecto(subida.getvalue())
            except (ValueError, FileNotFoundError) as exc:
                st.error(str(exc))
            else:
                st.session_state[_K_PENDIENTE] = estado
                st.rerun()


def render() -> None:
    with st.sidebar:
        _aplicar_carga_pendiente()            # antes de crear cualquier widget

        st.markdown("## BenchMark-MOEAs")
        st.divider()

        # ── Proyecto: nombre + guardar/cargar el snapshot de sesion ───────────
        st.markdown("### Proyecto")
        st.text_input("Nombre del proyecto", key=state.K_PROY)
        _controles_proyecto()

        st.divider()

        # ── Lectura de CSV (detalle plegado: no estorba la demo de flujo) ──────
        with st.expander("Lectura de CSV (avanzado)"):
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
        
            
        # ── Progreso / navegacion con gating ────────
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
        st.caption("Se desbloquean en orden.")

        st.divider()
        st.caption("v0.2 · evaluacion y visualizacion de PFAs")
