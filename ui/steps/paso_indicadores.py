# -*- coding: utf-8 -*-
"""
Paso 2 · INDICADORES: elegir indicadores y preprocesamiento. Al evaluar,
desbloquea el paso de Resultados.
"""
from __future__ import annotations

import numpy as np
import streamlit as st

from domain import evaluacion, indicators
from .. import state

# Texto para el atributo de Pareto-compliance (primera clase).
_COMP = {
    "strict": "STRICT Pareto-compliant",
    "weak": "WEAK Pareto-compliant",
    "no": "NO Pareto-compliant",
}

# Mapeo del widget de HV (radio del expander) al hv_modo de evaluacion.evaluar.
_HV_MODO = {
    "Automatico (nadir)": "nadir",
    "1.1 x nadir": "nadir_x1.1",
    "Manual": "fijo",
}

# Indicadores con computo REAL hoy: R2/Riesz/SPD lanzan NotImplementedError en
# domain.indicators.calcular, asi que NO se siembran por default (solo llenarian
# 'omitidos' sin producir resultados). Siguen disponibles en el catalogo para
# seleccionarlos a mano.
_IMPLEMENTADOS = ("HV", "IGD", "IGD+", "Dp", "Eps+")

# Clave del WIDGET multiselect. Streamlit la borra al desmontar el paso; la
# copia persistente es state.K_INDS, que vuelve a sembrarla al regresar.
_K_WIDGET_INDS = "inds_sel_widget"


def _default_indicadores(persistido, implementados=_IMPLEMENTADOS) -> list[str]:
    """
    PURA (testeable): siembra del multiselect de indicadores. Restaura la
    seleccion persistida (K_INDS) si existe; si viene vacia (o solo trae ids no
    implementados), cae al default = indicadores implementados. NUNCA devuelve
    ids fuera de `implementados` (p. ej. un R2 persistido de una sesion vieja).
    """
    base = [i for i in (persistido or []) if i in implementados]
    return base if base else list(implementados)


def _evaluar(seleccion: list[str]) -> None:
    """
    Corre el MOTOR con la seleccion sobre los PFA cargados. Si va bien, guarda
    resultados/omitidos y avanza al Paso 3; si falla por un error de USO
    (ValueError de evaluar) o de datos, lo muestra y NO avanza.
    """
    pfas = st.session_state.get(state.K_PFAS, [])
    if not pfas:
        st.error("No hay PFA cargados. Vuelve al Paso 1 (Datos) y sube tus "
                 ".pof o .zip antes de evaluar.")
        return

    # Punto de referencia de HV: solo se lee su widget si se pidio HV.
    hv_modo, hv_punto_fijo = "nadir_x1.1", None
    if "HV" in seleccion:
        hv_modo = _HV_MODO.get(st.session_state.get("hv_HV"), "nadir_x1.1")
        if hv_modo == "fijo":
            crudo = st.session_state.get("hvvec_HV", "")
            try:
                hv_punto_fijo = np.array(
                    [float(x) for x in crudo.split(",") if x.strip()], dtype=float)
            except ValueError:
                st.error("Vector de referencia de HV invalido: usa numeros "
                         "separados por coma (p. ej. 1.1, 1.1, 1.1).")
                return

    # Feedback en vivo: el motor invoca `progreso` al INICIO de cada escenario
    # (evaluar puede tardar minutos con indicadores de distancia; sin esto la
    # app parecia congelada).
    barra = st.progress(0.0, text="Preparando evaluación...")

    def _avance(hecho: int, total: int, etiqueta: str) -> None:
        barra.progress(hecho / total if total else 0.0,
                       text=f"Evaluando {etiqueta}  ({hecho + 1}/{total})")

    try:
        with st.spinner("Evaluando indicadores..."):
            resultados, omitidos = evaluacion.evaluar(
                pfas, seleccion,
                override=st.session_state.get(state.K_FREJ) or None,
                hv_modo=hv_modo, hv_punto_fijo=hv_punto_fijo,
                progreso=_avance)
    except ValueError as e:
        barra.empty()
        st.error(f"No se pudo evaluar: {e}. Sugerencia: usa 'Automatico' o "
                 "'1.1 x nadir' si el lote mezcla m.")
        return
    barra.progress(1.0, text="Evaluación completada")

    st.session_state[state.K_RES] = resultados
    st.session_state[state.K_OMIT] = omitidos
    st.session_state[state.K_INDS] = seleccion
    state.completar(1)
    state.ir_a(2)
    st.rerun()


def render() -> None:
    st.subheader("Paso 2 · Indicadores de calidad")
    st.caption("Elige los indicadores y evalúa.")

    todos = list(indicators.CATALOGO.values())
    nombre_por_id = {m.id: m.nombre for m in todos}

    st.markdown("#### Indicadores a evaluar")
    # El multiselect se desmonta al cambiar de paso y streamlit borra su clave:
    # se siembra desde K_INDS (la copia persistente) solo cuando falta, y abajo
    # se copia la seleccion de vuelta a K_INDS para restaurarla al volver.
    # (key fijo + siembra previa, NO default= dinamico: cambiar default cambia
    # la identidad del widget y se tragaria interacciones.)
    if _K_WIDGET_INDS not in st.session_state:
        st.session_state[_K_WIDGET_INDS] = _default_indicadores(
            st.session_state.get(state.K_INDS))
    seleccion = st.multiselect(
        "Indicadores", options=[m.id for m in todos],
        format_func=lambda i: nombre_por_id[i],
        label_visibility="collapsed", key=_K_WIDGET_INDS,
    )
    st.session_state[state.K_INDS] = seleccion

    st.divider()
    st.markdown("#### Parametros por indicador")
    if not seleccion:
        st.warning("Selecciona al menos un indicador.")
    for ind_id in seleccion:
        meta = indicators.CATALOGO[ind_id]
        with st.expander(meta.nombre, expanded=False):
            # Linea unica visible (sentido); el resto de la ficha va al tooltip.
            detalles = [meta.descripcion, _COMP[meta.compliance] + "."]
            if ind_id == "HV":
                detalles.append("Calculado via pymoo.")
            if meta.requiere_ref:
                detalles.append("Requiere frente de referencia (paso Datos).")
            sentido = ("mayor mejor (max)" if meta.sentido == "max"
                       else "menor mejor (min)")
            st.markdown(f"Sentido: **{sentido}**", help=" ".join(detalles))
            if ind_id == "HV":
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

    st.divider()
    c_atras, c_eval = st.columns([1, 2])
    if c_atras.button("Anterior", width="stretch"):
        state.ir_a(0)
        st.rerun()
    if c_eval.button("Evaluar indicadores", type="primary", width="stretch",
                     disabled=not seleccion):
        _evaluar(seleccion)
