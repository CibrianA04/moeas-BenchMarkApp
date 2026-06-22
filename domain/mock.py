# -*- coding: utf-8 -*-
"""
Generadores de datos de EJEMPLO (mock) DESHABILITADOS.
Devuelven listas y datos vacíos para que la interfaz se dibuje sin romperse.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Listas de ejemplo mínimas para que los selectbox (widgets) funcionen
MOEAS_DEMO = ["Sin datos"]
MOPS_DEMO = [("Sin datos", 0)]

def preview_df(n: int = 8, m: int = 3) -> pd.DataFrame:
    return pd.DataFrame()

def front_2d(forma: str = "convexo", n: int = 60) -> np.ndarray:
    return np.empty((0, 2))

def front_3d(n: int = 250) -> np.ndarray:
    return np.empty((0, 3))

def valor_indicador(ind_id: str, puntos: np.ndarray) -> float:
    return 0.0

def tabla_medias_desv(ind_id: str, moeas: list[str], mops: list[tuple[str, int]]):
    idx = pd.MultiIndex.from_tuples(mops, names=["MOP", "m"])
    df = pd.DataFrame(index=idx, columns=moeas)
    return df, df
