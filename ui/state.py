# -*- coding: utf-8 -*-
"""
Estado de la aplicacion y STEP GATING.

st.session_state es la UNICA fuente de verdad. Cada paso se desbloquea solo si
se completaron los anteriores.
"""
from __future__ import annotations

import streamlit as st

# Nombres de los pasos (orden = flujo de trabajo).
PASOS = ["Datos", "Indicadores", "Resultados", "Visualizacion"]

# Claves en session_state.
K_PASO = "paso"            # indice del paso actual (0..3)
K_COMP = "completado"      # lista de bool por paso
K_PROY = "proyecto_nombre"
K_SEP = "csv_separador"
K_DEC = "csv_decimal"
K_INDS = "indicadores_sel"  # ids de indicadores elegidos
K_PFAS = "pfas_cargados"    # list[PFA] cargados desde el zip / .pof sueltos
K_ERR = "pfas_errores"      # list[(archivo, motivo)] de los omitidos
K_FIRMA = "_firma_subida"   # firma de los archivos ya procesados (evita reprocesar)


def init_estado() -> None:
    """Inicializa claves por defecto (no sobreescribe lo ya presente)."""
    st.session_state.setdefault(K_PASO, 0)
    st.session_state.setdefault(K_COMP, [False, False, False, False])
    st.session_state.setdefault(K_PROY, "experimento_demo")
    st.session_state.setdefault(K_SEP, "Coma  ( , )")
    st.session_state.setdefault(K_DEC, "Punto  ( . )")
    st.session_state.setdefault(K_INDS, [])
    st.session_state.setdefault(K_PFAS, [])
    st.session_state.setdefault(K_ERR, [])


def paso_actual() -> int:
    return st.session_state[K_PASO]


def completar(i: int) -> None:
    """Marca el paso i como completado (desbloquea el siguiente)."""
    comp = list(st.session_state[K_COMP])
    comp[i] = True
    st.session_state[K_COMP] = comp


def esta_completo(i: int) -> bool:
    return st.session_state[K_COMP][i]


def puede_ir_a(i: int) -> bool:
    """
    MAQUETA: todo DESBLOQUEADO para poder mostrar libremente cada paso del flujo.
    (A futuro: gating real -> entrar al paso i solo si los anteriores estan
    completos: `return all(st.session_state[K_COMP][:i])`.)
    """
    return True


def ir_a(i: int) -> None:
    """Cambia al paso i (en la maqueta no hay restriccion de navegacion)."""
    if puede_ir_a(i):
        st.session_state[K_PASO] = i
