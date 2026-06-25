# -*- coding: utf-8 -*-
"""
Indicadores de calidad: catalogo + interfaz de calculo (STUB).

Pareto-compliance es un atributo de PRIMERA CLASE: solo los indicadores
compliant (estricta/debil) permiten conclusiones fuertes. HV e IGD+ lo son;
IGD, GD, MS no.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import mock


@dataclass(frozen=True)
class MetaIndicador:
    id: str
    nombre: str          # texto para mostrar en la UI
    sentido: str         # "max" (mayor mejor) | "min" (menor mejor)
    requiere_ref: bool   # necesita frente de referencia
    compliance: str      # "estricta" | "debil" | "no"
    grupo: str           # "principal" | "secundario"
    descripcion: str = ""


# Catalogo. Punto de EXTENSION: agregar un indicador = agregar una entrada aqui
# (y, en la version real, su rama en calcular()).
CATALOGO: dict[str, MetaIndicador] = {
    "HV":    MetaIndicador("HV", "HV (Hypervolume)", "max", False, "strict", "principal",
                           "Volumen dominado respecto a un punto de referencia."),
    "IGD":   MetaIndicador("IGD", "IGD (Inverted Generational Distance)", "min", True, "no", "principal",
                           "Distancia media del frente de referencia al PFA."),
    "IGD+":  MetaIndicador("IGD+", "IGD+ (IGD modificado)", "min", True, "weak", "principal",
                           "Variante de IGD"),
    "R2":    MetaIndicador("R2", "R2", "min", True, "weak", "principal",
                           ""),
    "Dp":    MetaIndicador("Dp", "Delta p", "min", True, "no", "principal",
                           "Distancia de Hausdorff promediada (combina GD e IGD)."),
    "Eps+":  MetaIndicador("Eps+", "Epsilon+ (aditivo)", "min", True, "weak", "principal",
                           "Minimo desplazamiento aditivo para dominar la referencia."),
    "Riesz": MetaIndicador("Riesz", "Riesz s-energy", "min", False, "no", "secundario",
                           "Energia de pares: mide uniformidad de la distribucion."),
    "SPD":   MetaIndicador("SPD", "Solow-Polasky (SPD)", "max", False, "no", "secundario",
                           "Diversidad del conjunto de soluciones."),
}


def principales() -> list[MetaIndicador]:
    return [m for m in CATALOGO.values() if m.grupo == "principal"]


def secundarios() -> list[MetaIndicador]:
    return [m for m in CATALOGO.values() if m.grupo == "secundario"]


def calcular(ind_id: str, puntos: np.ndarray,
             ref: np.ndarray | None = None, **params) -> float:
    """
    STUB: devuelve un valor de EJEMPLO.

    FUTURO:
      - HV: via pymoo (interfaz lista para cambiar a un binario en C).
      - IGD/IGD+/R2/Delta p/Epsilon+: implementacion en Python/numpy; requieren 'ref'.
      - Riesz/SPD: no requieren referencia.
      - Validar requiere_ref, normalizar y manejar DRS antes de calcular.
    """
    meta = CATALOGO[ind_id]
    if meta.requiere_ref and ref is None:
        # FUTURO: lanzar/avisar; 
        pass
    return mock.valor_indicador(ind_id, puntos)


def _hv_pymoo(puntos: np.ndarray, punto_ref: np.ndarray) -> float:
    """STUB del backend de HV. FUTURO: pymoo o binario en C."""
    raise NotImplementedError("Backend de HV pendiente (pymoo / binario en C).")
