# -*- coding: utf-8 -*-
"""
Estadistica: agregacion de corridas y pruebas de significancia (STUBS).

Eleccion de prueba SEGUN ESCENARIO:
    - pareado       -> Wilcoxon (rangos con signo)
    - independiente -> Mann-Whitney U
    - multi (3+)    -> Friedman + post-hoc (Nemenyi / Holm) + Critical Differences
"""
from __future__ import annotations

import numpy as np

from .model import CORRIDAS_MINIMAS

PRUEBA_POR_ESCENARIO = {
    "pareado": "Wilcoxon (rangos con signo)",
    "independiente": "Mann-Whitney U",
    "multi": "Friedman + post-hoc (Nemenyi / Holm)",
}


def agregar(valores) -> tuple[float, float]:
    """Devuelve (media, desviacion estandar) sobre las corridas. Trivial y seguro."""
    a = np.asarray(list(valores), dtype=float)
    if a.size == 0:
        return float("nan"), float("nan")
    desv = float(a.std(ddof=1)) if a.size > 1 else 0.0
    return float(a.mean()), desv


def corridas_insuficientes(n: int, minimo: int = CORRIDAS_MINIMAS) -> bool:
    """True si hay muy pocas corridas para una conclusion confiable."""
    return n < minimo


def recomendar_prueba(escenario: str) -> str:
    """Devuelve el nombre de la prueba adecuada para el escenario dado."""
    return PRUEBA_POR_ESCENARIO.get(escenario, "Wilcoxon (rangos con signo)")


def comparar(valores_a, valores_b, escenario: str, alpha: float = 0.05) -> str:
    """
    STUB: compara dos MOEAs y devuelve un simbolo '+', '-' o '='.
    FUTURO: usar scipy.stats (wilcoxon / mannwhitneyu) segun escenario.
    """
    raise NotImplementedError("Prueba estadistica pendiente (scipy.stats).")


def critical_differences(rankings) -> "object":
    """STUB: datos para el Critical Differences plot. FUTURO: Friedman + post-hoc."""
    raise NotImplementedError("Critical Differences pendiente.")
