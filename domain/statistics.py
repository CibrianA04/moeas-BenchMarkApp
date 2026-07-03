# -*- coding: utf-8 -*-
"""
Estadistica de apoyo para la UI y el graficado. NO es la fuente de la tabla final.

Contrato (ver CLAUDE.md §5): la FUENTE UNICA de la tabla oficial (medias, Wilcoxon,
ranking, LaTeX) es el script del doctor `createIndicatorTable.R`. Este modulo NO
reimplementa ranking ni LaTeX; solo ofrece, consumiendo la salida de
`evaluacion.evaluar` ({mop, m, N, moea, indicador, valores:[...por corrida...]}):
  (a) resumen():        media/desviacion por (MOP, m, N, indicador, MOEA) para la UI.
  (b) corrida_mediana(): la corrida MEDIANA por indicador (R no la da; hace falta
                         para graficar el frente "tipico").
  (c) significancia():  un PREVIEW con la MISMA config del R (Mann-Whitney U, una
                        cola hacia el ganador, alpha=0.05, sin correccion multiple).
                        La tabla autoritativa la sigue dando R.

Eleccion de prueba SEGUN ESCENARIO (referencia):
    - pareado       -> Wilcoxon (rangos con signo)
    - independiente -> Mann-Whitney U
    - multi (3+)    -> Friedman + post-hoc (Nemenyi / Holm) + Critical Differences
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import indicators
from .model import CORRIDAS_MINIMAS

PRUEBA_POR_ESCENARIO = {
    "pareado": "Wilcoxon (rangos con signo)",
    "independiente": "Mann-Whitney U",
    "multi": "Friedman + post-hoc (Nemenyi / Holm)",
}


def agregar(valores) -> tuple[float, float]:
    """Devuelve (media, desviacion estandar) sobre las corridas."""
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


# ─────────────────────────────────────────────────────────────────────────────
#  Consumo de la salida de evaluacion.evaluar. Cada dict de entrada ya viene por
#  (MOP, m, N, MOEA, indicador) con `valores` = un valor por corrida.
# ─────────────────────────────────────────────────────────────────────────────
_COLS_RESUMEN = ["mop", "m", "N", "indicador", "moea", "media", "desv", "n"]


def resumen(resultados) -> pd.DataFrame:
    """
    Media y desviacion estandar (muestral, ddof=1 como el sd() de R) por
    (MOP, m, N, indicador, MOEA). `n` = numero de corridas.

    Es para MOSTRAR en la UI; la media OFICIAL de la tabla la produce el script R.
    """
    filas = []
    for r in resultados:
        media, desv = agregar(r["valores"])
        filas.append({
            "mop": r["mop"], "m": r["m"], "N": r["N"],
            "indicador": r["indicador"], "moea": r["moea"],
            "media": media, "desv": desv, "n": len(r["valores"]),
        })
    return pd.DataFrame(filas, columns=_COLS_RESUMEN)


# CONVENCION (ajustable): con n PAR se toma la mediana INFERIOR, es decir el
# elemento en el indice floor((n-1)/2) tras ordenar. Si el doc prefiere la
# superior, cambiar a n // 2.
def indice_mediana(valores) -> int:
    """
    Indice (posicion en `valores`) de la corrida cuyo valor es la MEDIANA del
    conjunto. Con n par -> mediana INFERIOR (indice floor((n-1)/2) del orden).

    `valores` viene ordenado por corrida desde `evaluacion.evaluar`, asi que el
    indice devuelto identifica la corrida (su etiqueta = esa posicion). Ver la
    nota de CONVENCION de arriba (ajustable a mediana superior).
    """
    a = np.asarray(list(valores), dtype=float)
    if a.size == 0:
        raise ValueError("Sin valores: no existe corrida mediana.")
    k = (a.size - 1) // 2                      # floor((n-1)/2): mediana inferior si n par
    orden = np.argsort(a, kind="stable")       # estable: desempata por orden original
    return int(orden[k])


_COLS_MEDIANA = ["mop", "m", "N", "indicador", "moea", "indice", "valor"]


def corrida_mediana(resultados) -> pd.DataFrame:
    """
    Por (MOP, m, N, indicador, MOEA), identifica la corrida MEDIANA (mediana POR
    ese indicador). Devuelve `indice` (posicion en `valores` = etiqueta de corrida)
    y su `valor`. Sirve para graficar el frente "tipico" (R no da la mediana).
    """
    filas = []
    for r in resultados:
        idx = indice_mediana(r["valores"])
        filas.append({
            "mop": r["mop"], "m": r["m"], "N": r["N"],
            "indicador": r["indicador"], "moea": r["moea"],
            "indice": idx, "valor": float(r["valores"][idx]),
        })
    return pd.DataFrame(filas, columns=_COLS_MEDIANA)


_COLS_SIGNIF = ["mop", "m", "N", "indicador", "sentido", "ganador",
                "media_ganador", "rival", "media_rival", "p_value",
                "alternativa", "significativo"]


def significancia(resultados, alpha: float = 0.05) -> pd.DataFrame:
    """
    PREVIEW de significancia por (MOP, m, N, indicador). NO es autoritativo: la
    tabla oficial (con su Wilcoxon y ranking) la produce el script R del doctor.
    Se replica su MISMA config para que el preview sea coherente:

    - Ganador = MOEA con la MEJOR media segun CATALOGO[indicador].sentido
      ('max' -> media mayor; 'min' -> media menor).
    - Mann-Whitney U (muestras INDEPENDIENTES), UNA cola hacia el ganador
      (alternative 'greater' si 'max', 'less' si 'min'), SIN correccion multiple.
    - Ganador contra CADA rival; marca `significativo` si p <= alpha (0.05).

    Grupos con < 2 MOEAs se omiten (no hay con quien comparar).
    """
    from scipy.stats import mannwhitneyu       # import perezoso (dependencia real)

    # Agrupar por (MOP, m, N, indicador) -> {moea: valores} (orden de aparicion).
    grupos: dict[tuple, dict[str, list]] = {}
    for r in resultados:
        clave = (r["mop"], r["m"], r["N"], r["indicador"])
        grupos.setdefault(clave, {})[r["moea"]] = r["valores"]

    filas = []
    for (mop, m, n_pob, indicador), por_moea in grupos.items():
        if len(por_moea) < 2:
            continue                            # sin rival: no hay comparacion
        sentido = indicators.CATALOGO[indicador].sentido
        medias = {moea: float(np.mean(v)) for moea, v in por_moea.items()}
        if sentido == "max":
            ganador, alternativa = max(medias, key=medias.get), "greater"
        else:
            ganador, alternativa = min(medias, key=medias.get), "less"

        vals_ganador = np.asarray(por_moea[ganador], dtype=float)
        for rival, vals_rival in por_moea.items():
            if rival == ganador:
                continue
            try:
                p = float(mannwhitneyu(
                    vals_ganador, np.asarray(vals_rival, dtype=float),
                    alternative=alternativa).pvalue)
            except ValueError:
                p = float("nan")                # p. ej. todas las muestras identicas
            filas.append({
                "mop": mop, "m": m, "N": n_pob, "indicador": indicador,
                "sentido": sentido, "ganador": ganador,
                "media_ganador": medias[ganador], "rival": rival,
                "media_rival": medias[rival], "p_value": p,
                "alternativa": alternativa,
                "significativo": bool(p <= alpha),   # NaN <= alpha -> False
            })
    return pd.DataFrame(filas, columns=_COLS_SIGNIF)
