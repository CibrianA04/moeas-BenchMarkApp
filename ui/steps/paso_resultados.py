# -*- coding: utf-8 -*-
"""
Paso 3 · RESULTADOS: tabla por indicador (mejor media resaltada), pruebas
estadisticas por escenario y exportacion (CSV / LaTeX).

Consume la salida del motor (`state.K_RES`/`state.K_OMIT`, producida en el Paso 2
por `domain.evaluacion.evaluar`) y la presenta con `domain.tables` /
`domain.statistics`. La app NO recalcula estadistica aqui: solo la muestra.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from domain import indicators, statistics, tables
from .. import components, state

# Estilo del resaltado de la mejor media (rank 1) de cada fila.
_RESALTE = "background-color: rgba(33, 150, 83, 0.35); font-weight: 700;"


def tabla_display(est: pd.DataFrame,
                  moeas: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    PURA (sin streamlit; testeable): aplana la tabla estructurada de
    `tables.tabla_estructurada` a un DataFrame de presentacion + su mascara.

    - display: columnas MOP, m, N + una por MOEA con "media (desv)" en notacion
      cientifica, o "N/A" si falta el dato de esa (MOP, m, N, MOEA).
    - mask: mismas columnas; True donde ese MOEA es rank 1 de la fila (para
      resaltarlo). Las columnas MOP/m/N nunca se resaltan.
    """
    filas, marcas = [], []
    for _, fila in est.iterrows():
        d = {"MOP": fila[("MOP", "")], "m": fila[("m", "")], "N": fila[("N", "")]}
        mk = {"MOP": False, "m": False, "N": False}
        for mo in moeas:
            rank = fila[(mo, "rank")]
            if pd.isna(rank):
                d[mo], mk[mo] = "N/A", False
            else:
                d[mo] = f"{fila[(mo, 'media')]:.3e} ({fila[(mo, 'desv')]:.3e})"
                mk[mo] = int(rank) == 1
        filas.append(d)
        marcas.append(mk)
    cols = ["MOP", "m", "N", *moeas]
    return (pd.DataFrame(filas, columns=cols),
            pd.DataFrame(marcas, columns=cols))


def _mostrar_tabla(est: pd.DataFrame, moeas: list[str]) -> None:
    """Dibuja la tabla plana con la mejor media de cada fila resaltada."""
    display, mask = tabla_display(est, moeas)
    estilos = pd.DataFrame(np.where(mask.to_numpy(), _RESALTE, ""),
                           index=display.index, columns=display.columns)
    styler = display.style.apply(lambda _: estilos, axis=None)
    st.dataframe(styler, width="stretch", hide_index=True)


def _mostrar_significancia(resultados: list[dict], ind_id: str,
                           filtro_n: int | None) -> None:
    """Evidencia +/-/= por escenario (Mann-Whitney hacia el ganador)."""
    sig = statistics.significancia(
        [r for r in resultados if r["indicador"] == ind_id])
    if filtro_n is not None and not sig.empty:
        sig = sig[sig["N"] == filtro_n]
    if sig.empty:
        st.caption("Sin comparaciones: se necesitan >= 2 MOEAs por escenario "
                   "(MOP, m, N).")
        return
    vista = sig.copy()
    vista.insert(0, "escenario",
                 vista["mop"] + " - m=" + vista["m"].astype(str)
                 + " - N=" + vista["N"].astype(str))
    vista = vista[["escenario", "ganador", "rival", "p_value", "significativo"]]
    st.dataframe(vista, width="stretch", hide_index=True)
    st.caption("Mann-Whitney U de una cola hacia el ganador, alpha=0.05, sin "
               "correccion multiple (mismo criterio que la marca # de la tabla).")


def _mostrar_omitidos() -> None:
    """Expander con lo que el motor NO calculo (sin frente ref / corrida mala)."""
    omit = st.session_state.get(state.K_OMIT) or []
    if not omit:
        return
    with st.expander(f"No calculado: {len(omit)} aviso(s)", expanded=False):
        sin_ref = [o for o in omit if o.get("tipo") == "sin_referencia"]
        fallidas = [o for o in omit if o.get("tipo") == "corrida_fallida"]
        if sin_ref:
            st.markdown("**Escenarios sin frente de referencia** (se omiten sus "
                        "indicadores basados en distancia):")
            st.dataframe(pd.DataFrame(sin_ref), width="stretch", hide_index=True)
        if fallidas:
            st.markdown("**Corridas que fallaron al calcular un indicador:**")
            st.dataframe(pd.DataFrame(fallidas), width="stretch", hide_index=True)


def _botones_navegacion() -> None:
    st.divider()
    c_atras, c_sig = st.columns([1, 2])
    if c_atras.button("Anterior", width="stretch"):
        state.ir_a(1)
        st.rerun()
    if c_sig.button("Ir a Visualizacion", type="primary", width="stretch"):
        state.ir_a(3)
        st.rerun()


def render() -> None:
    st.subheader("Paso 3 · Resultados y tablas")
    st.caption("UNA tabla por indicador. La mejor media de cada fila se "
               "resalta; debajo, pruebas estadisticas por escenario.")

    # Visitar este paso lo marca como completado (avance del flujo).
    state.completar(2)

    resultados = st.session_state.get(state.K_RES, [])
    if not resultados:
        st.info("Aun no hay resultados. Ve al Paso 2 y pulsa "
                "'Evaluar indicadores'.")
        _botones_navegacion()
        return

    nombres = {m.id: m.nombre for m in indicators.CATALOGO.values()}
    # Indicadores realmente evaluados (o los elegidos como respaldo) y MOEAs.
    elegidos = st.session_state.get(state.K_INDS) or sorted(
        {r["indicador"] for r in resultados})
    moeas = sorted({r["moea"] for r in resultados})

    c1, c2 = st.columns([2, 1])
    ind_id = c1.selectbox("Indicador", elegidos, format_func=lambda i: nombres[i])
    ns = sorted({r["N"] for r in resultados if r["indicador"] == ind_id})
    sel_n = c2.selectbox("N (poblacion)", ["Todas", *ns])
    filtro_n = None if sel_n == "Todas" else int(sel_n)

    meta = indicators.CATALOGO[ind_id]
    if meta.compliance == "no":
        st.warning("Indicador NO Pareto-compliant.")
    else:
        st.success(f"Pareto-compliant ({meta.compliance}).")

    # ── Tabla real por indicador ───────────────────────────────────────────────
    est = tables.tabla_estructurada(resultados, ind_id, moeas=moeas,
                                    filtro_n=filtro_n)
    datos = None
    if est.empty:
        st.warning(f"No hay datos de {nombres[ind_id]} con este filtro. Puede que "
                   "el indicador no se calculara (p. ej. sin frente de referencia).")
    else:
        _mostrar_tabla(est, moeas)
        proyecto = st.session_state.get(state.K_PROY, "experimento")
        caption = f"Desempeno segun {nombres[ind_id]}"
        datos = {
            "CSV": (tables.a_csv_doc(est),
                    f"{proyecto}_{ind_id}.csv", "text/csv"),
            "LaTeX (.tex)": (
                tables.a_latex_doc(est, ind_id, caption,
                                   f"tab:{ind_id}").encode("utf-8"),
                f"{proyecto}_{ind_id}.tex", "text/plain"),
        }

    st.markdown("##### Descargar tabla")
    components.descargas("tabla", ["CSV", "LaTeX (.tex)", "Markdown"],
                         datos_por_formato=datos)

    st.divider()

    # ── Pruebas de desempeno: evidencia estadistica del indicador/filtro ───────
    st.markdown("#### Pruebas de desempeno")
    _mostrar_significancia(resultados, ind_id, filtro_n)

    _mostrar_omitidos()

    st.markdown("##### Critical Differences plot (futuro)")
    st.caption("Ranking de MOEAs y grupos sin diferencia significativa.")
    components.descargas("cd_plot", ["PNG", "SVG", "EPS", "TikZ (.tex)"])

    _botones_navegacion()
