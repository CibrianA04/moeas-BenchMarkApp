# -*- coding: utf-8 -*-
"""
Paso 4 · VISUALIZACION: graficar el frente de la corrida MEDIANA (lo que pide el
doc: no se grafica una corrida cualquiera, sino la asociada a la mediana del
indicador; HV por defecto). Si aun no hay resultados del Paso 2, se puede elegir
la corrida a mano. La figura la construye domain/figures (headless, estilo del
doc); aqui solo se muestra y se descarga (PNG/SVG/EPS, y .tex si hay LaTeX).
"""
from __future__ import annotations

import streamlit as st

from domain import figures, statistics
from .. import components, state

# PNG por defecto (prioritario); TikZ (.tex) via backend PGF: se deshabilita
# solo si no hay LaTeX instalado (guardar_figura devuelve None).
FORMATOS = ["PNG", "SVG", "EPS", "TikZ (.tex)"]
_EXT_MIME = {
    "PNG": ("png", "image/png"),
    "SVG": ("svg", "image/svg+xml"),
    "EPS": ("eps", "application/postscript"),
    "TikZ (.tex)": ("tex", "application/x-tex"),
}


def _pfa_corrida_mediana(pfas, omitidos, mop, m, n_pob, moea, indicador, indice):
    """
    Localiza el PFA cuya posicion en `valores` fue `indice`, reconstruyendo el
    contrato de evaluacion.evaluar: `valores` va ordenado por numero de corrida
    y SIN las corridas que fallaron para ese indicador (tipo 'corrida_fallida').
    Devuelve None si no se puede reconstruir (p. ej. se recargaron los datos).
    """
    grupo = sorted(
        (p for p in pfas if (p.mop, p.m, p.n, p.moea) == (mop, m, n_pob, moea)),
        key=lambda p: p.corrida)
    fallidas = {
        o.get("corrida") for o in (omitidos or [])
        if o.get("tipo") == "corrida_fallida"
        and (o.get("mop"), o.get("m"), o.get("N"), o.get("moea"),
             o.get("indicador")) == (mop, m, n_pob, moea, indicador)
    }
    exitosas = [p for p in grupo if p.corrida not in fallidas]
    if 0 <= indice < len(exitosas):
        return exitosas[indice]
    return None


def _mostrar_figura(pfa, titulo: str) -> None:
    """Dibuja el frente (2D/3D directo; m>3 con método a elegir) y cablea las
    descargas reales de la figura."""
    st.markdown("#### Figura")
    # El DOMINIO construye la figura (ports headless del estilo del doc).
    # Cada dimension ofrece sus vistas posibles; la primera (Dispersión) es el
    # default. Keys distintas por caso para no confundir los selectbox.
    if pfa.m == 2:
        metodo = st.selectbox("Método de visualización",
                              figures.METODOS_M2, key="viz_metodo_m2")
    elif pfa.m == 3:
        metodo = st.selectbox("Método de visualización",
                              figures.METODOS_M3, key="viz_metodo_m3")
    else:
        metodo = st.selectbox("Método de visualización (m>3)",
                              figures.METODOS_M4, key="viz_metodo")
    fig = figures.figura_frente(pfa.puntos, pfa.m, metodo=metodo, titulo=titulo)
    st.pyplot(fig)

    base = (pfa.archivo.rsplit(".", 1)[0] if pfa.archivo else
            f"{pfa.moea}_{pfa.mop}_{pfa.m:02d}D_N{pfa.n}_R{pfa.corrida:02d}")
    datos = {}
    for etiqueta, (ext, mime) in _EXT_MIME.items():
        contenido = figures.guardar_figura(fig, etiqueta)
        if contenido is not None:
            datos[etiqueta] = (contenido, f"{base}.{ext}", mime)
    figures.cerrar(fig)                               # tras exportar los bytes

    st.markdown("##### Descargar figura")
    components.descargas("figura", FORMATOS, datos_por_formato=datos)
    if not figures.hay_latex():
        st.caption("El .tex requiere una instalación de LaTeX (p. ej. MiKTeX).")


def _render_mediana(pfas, resultados) -> None:
    """Flujo principal: elegir escenario/MOEA/indicador y graficar la MEDIANA."""
    med = statistics.corrida_mediana(resultados)

    c1, c2, c3 = st.columns(3)
    escenarios = sorted({(r["mop"], r["m"], r["N"]) for r in resultados})
    esc = c1.selectbox("Escenario (MOP · m · N)", escenarios,
                       format_func=lambda e: f"{e[0]} · m={e[1]} · N={e[2]}",
                       key="viz_esc")
    mop, m, n_pob = esc
    moeas = sorted({r["moea"] for r in resultados
                    if (r["mop"], r["m"], r["N"]) == esc})
    moea = c2.selectbox("MOEA", moeas, key="viz_moea")
    inds = sorted({r["indicador"] for r in resultados
                   if (r["mop"], r["m"], r["N"]) == esc and r["moea"] == moea})
    idx_hv = inds.index("HV") if "HV" in inds else 0   # default: mediana por HV
    ind_id = c3.selectbox("Indicador de la mediana", inds, index=idx_hv,
                          key="viz_ind",
                          help="Se grafica la corrida MEDIANA segun este "
                               "indicador (el frente 'tipico'), no una corrida "
                               "arbitraria.")

    sel = med[(med["mop"] == mop) & (med["m"] == m) & (med["N"] == n_pob)
              & (med["moea"] == moea) & (med["indicador"] == ind_id)]
    if sel.empty:
        st.warning("No hay corrida mediana para esa combinación.")
        return
    fila = sel.iloc[0]

    # Nota: tras el fix del punto de referencia de HV (margen sobre el RANGO,
    # robusto a objetivos negativos), la mediana por HV en VNT2/VNT3 vuelve a
    # ser fiable; si esa politica cambia al confirmarla con el doc, revisar esto.
    pfa = _pfa_corrida_mediana(pfas, st.session_state.get(state.K_OMIT),
                               mop, m, n_pob, moea, ind_id, int(fila["indice"]))
    if pfa is None:
        st.warning("No se pudo localizar el PFA de la corrida mediana entre los "
                   "archivos cargados (¿se recargaron los datos tras evaluar?).")
        return

    st.caption(f"Corrida mediana según {ind_id}: **R{pfa.corrida:02d}** "
               f"(valor = {fila['valor']:.3e})")
    st.divider()
    titulo = f"{moea} · {mop} (mediana por {ind_id}, R{pfa.corrida:02d})"
    _mostrar_figura(pfa, titulo)


def _render_manual(pfas) -> None:
    """Fallback sin resultados: elegir la corrida a mano (comportamiento previo)."""
    st.info("Aún no hay resultados del Paso 2: elige la corrida a mano. Evalúa "
            "indicadores para graficar la corrida MEDIANA (la que pide el doc).")
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
    titulo = f"{pfa.moea} · {pfa.mop} · corrida {pfa.corrida}  (m={pfa.m}, N={pfa.n})"
    _mostrar_figura(pfa, titulo)


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

    resultados = st.session_state.get(state.K_RES, [])
    if resultados:
        _render_mediana(pfas, resultados)
    else:
        _render_manual(pfas)

    st.divider()
    if st.button("Anterior", width="stretch"):
        state.ir_a(2)
        st.rerun()
