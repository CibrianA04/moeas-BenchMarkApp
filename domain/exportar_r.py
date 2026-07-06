# -*- coding: utf-8 -*-
"""
Exportador al formato/ruta EXACTOS que lee el script del doctor
CreateIndicator/createIndicatorTable.R. La app NO calcula medias/Wilcoxon/tabla
(eso lo hace R, fuente unica de verdad; ver CLAUDE.md §5): aqui SOLO se escriben
los valores de indicador POR CORRIDA en el arbol que ese script consume.

Ruta que espera el R (de su propio codigo, linea 64):
    {dirOut}/{MOEA}/{card}/{MOEA}_{MOP}_{m:02d}D.{ext}
  - Cada archivo: UNA columna, un valor por linea, un valor por corrida, SIN
    cabecera (el R hace read.table(header=FALSE) y usa la columna V1).
  - card = bucket de cardinalidad/poblacion; aqui "N{n}" (p. ej. N200). Debe
    COINCIDIR con el argumento CARD que se pase al script.
  - MOP del nombre = el nombre que usa el R = VIE (VNT2->VIE2, VNT3->VIE3),
    reutilizando el mapeo de data/csv_io.py; los demas MOP pasan igual (el propio
    R lista "VIE1"/"VIE2"/"VIE3" en sus MOPs).
  - ext = token de archivo seguro por indicador (IGD+ -> IGDplus, etc.).

Entrada: la salida de domain.evaluacion.evaluar (lista de dicts
{mop, m, N, moea, indicador, valores:[...un valor por corrida...]}).
"""
from __future__ import annotations

from pathlib import Path

from data import csv_io

from . import indicators

# Token de archivo seguro por indicador (evita el '+' en el nombre de archivo).
# Para ids no listados se cae a ind_id.replace("+", "plus"), que produce estos mismos.
EXT_POR_INDICADOR = {
    "HV": "HV", "IGD": "IGD", "IGD+": "IGDplus", "Eps+": "Epsplus", "Dp": "Dp",
}


def token_extension(ind_id: str) -> str:
    """Extension de archivo segura para el indicador (IGD+ -> IGDplus, Eps+ -> Epsplus)."""
    return EXT_POR_INDICADOR.get(ind_id, ind_id.replace("+", "plus"))


def _mop_para_r(mop: str) -> str:
    """MOP tal como lo nombra el R: aplica el mapeo VNT->VIE de csv_io (los demas igual)."""
    return csv_io.MAPEO_MOP_REF_DEFAULT.get(mop, mop)


def exportar(resultados, dir_out) -> dict:
    """
    Escribe el arbol {dir_out}/{MOEA}/{card}/{MOEA}_{MOP}_{m:02d}D.{ext}: un valor por
    corrida (un float por linea, alta precision via repr, SIN cabecera).

    - card = "N{N}"; MOP mapeado VNT->VIE; ext = token seguro del indicador.
    - Tolerante: un grupo SIN valores se OMITE (no se escribe su archivo), sin abortar.
    - Devuelve un MANIFIESTO por indicador exportado:
        {ind_id: {"token": <ext>, "MUST_MAXIMIZE": 1|0}}
      con MUST_MAXIMIZE = 1 si CATALOGO[ind].sentido == 'max' else 0, para saber como
      invocar el R (una corrida del script por indicador).
    """
    raiz = Path(dir_out)
    manifiesto: dict[str, dict] = {}

    for r in resultados:
        valores = r.get("valores") or []
        if not valores:
            continue                                   # grupo incompleto: no se escribe

        ind_id = r["indicador"]
        ext = token_extension(ind_id)
        carpeta = raiz / r["moea"] / f"N{r['N']}"
        carpeta.mkdir(parents=True, exist_ok=True)

        nombre = f"{r['moea']}_{_mop_para_r(r['mop'])}_{r['m']:02d}D.{ext}"
        contenido = "".join(f"{float(v)!r}\n" for v in valores)
        (carpeta / nombre).write_text(contenido, encoding="utf-8")

        if ind_id not in manifiesto:
            sentido = indicators.CATALOGO[ind_id].sentido
            manifiesto[ind_id] = {
                "token": ext,
                "MUST_MAXIMIZE": 1 if sentido == "max" else 0,
            }

    return manifiesto
