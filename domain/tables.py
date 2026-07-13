# -*- coding: utf-8 -*-
r"""
Tabla de desempeno por indicador: traduccion a Python del script del doctor
`CreateIndicator/createIndicatorTable.R`. UNA tabla por indicador (no mezclar:
escalas y direcciones distintas, y las pruebas corren por indicador).

Pipeline en dos etapas:
  1) tabla_estructurada(): DataFrame con filas (MOP, m, N) y, por MOEA, sus
     media/desv/rank/sig (media/desv de statistics.resumen, rank de
     statistics.ranking, marcas de statistics.significancia; la direccion
     max/min sale de indicators.CATALOGO, nunca hardcodeada).
  2) a_latex_doc() / a_csv_doc(): renderizadores que consumen esa tabla.

PREAMBULO LaTeX requerido por el .tex generado (ponerlo en el documento que
lo incluya; son los mismos comandos que asume el script R):

    \usepackage{multirow}
    \usepackage{colortbl}    % o bien: \usepackage[table]{xcolor}
    \newcommand{\specialcell}[2][c]{\begin{tabular}[#1]{@{}c@{}}#2\end{tabular}}

`exportar_r.py` + el script R quedan como ORACULO de validacion: exportar los
valores por corrida y correr el R debe dar el mismo ranking y la misma tabla.
Devuelve DataFrames, cadenas y bytes; no importa Streamlit.
"""
from __future__ import annotations

import re

import pandas as pd

from . import indicators, statistics

# Columnas indice de la tabla estructurada (nivel 0 del MultiIndex de columnas).
_BASE = ("MOP", "m", "N")
# Campos por MOEA (nivel 1 del MultiIndex de columnas).
_CAMPOS = ("media", "desv", "rank", "sig")


def _esc(texto: str) -> str:
    """Escapa caracteres especiales de LaTeX en nombres (p. ej. Two_Arch2)."""
    return re.sub(r"([&%#_])", r"\\\1", str(texto))


def _moeas_de(estructurada: pd.DataFrame) -> list[str]:
    """Orden de columnas MOEA de la tabla estructurada (nivel 0, sin las base)."""
    return [c for c in estructurada.columns.get_level_values(0).unique()
            if c not in _BASE]


def tabla_estructurada(resultados, ind_id: str,
                       moeas: list[str] | None = None,
                       filtro_n: int | dict[str, int] | None = None) -> pd.DataFrame:
    """
    Tabla estructurada de UN indicador: una fila por (MOP, m, N) ordenada por
    esa tupla; por cada MOEA las columnas (moea, media|desv|rank|sig).

    - `resultados`: salida de evaluacion.evaluar (valores por corrida).
    - `moeas`: orden de columnas. None -> MOEAs unicos ordenados (sorted).
      Un MOEA listado sin datos produce celdas faltantes (render N/A), igual
      que el file.exists() del R con su universo fijo de MOEAs.
    - `filtro_n`: None -> todas las combinaciones (MOP, m, N); un int -> solo
      ese N para todos los MOP; un dict {mop: N} -> un N canonico por MOP y
      los MOP no listados se omiten (la vista publicable).
    - `sig` = True si el GANADOR de esa fila vence significativamente a ese
      MOEA (significancia() ya excluye al ganador: nunca lleva marca).
    - Celda sin datos -> todos sus campos son NA (el render la vuelve `N/A`).
    """
    if ind_id not in indicators.CATALOGO:
        raise KeyError(f"Indicador desconocido: '{ind_id}'.")

    sub = [r for r in resultados if r["indicador"] == ind_id]
    if isinstance(filtro_n, dict):
        sub = [r for r in sub
               if r["mop"] in filtro_n and r["N"] == filtro_n[r["mop"]]]
    elif filtro_n is not None:
        sub = [r for r in sub if r["N"] == int(filtro_n)]

    moeas = sorted({r["moea"] for r in sub}) if moeas is None else list(moeas)

    # Estadisticos por (MOP, m, N, MOEA) reutilizando statistics (nada se recalcula).
    stats: dict[tuple, dict] = {}
    for t in statistics.resumen(sub).itertuples(index=False):
        stats[(t.mop, t.m, t.N, t.moea)] = {"media": t.media, "desv": t.desv}
    for t in statistics.ranking(sub).itertuples(index=False):
        stats[(t.mop, t.m, t.N, t.moea)]["rank"] = int(t.rank)
    sig_si = set()                       # (mop, m, N, rival) vencidos con p <= alpha
    for t in statistics.significancia(sub).itertuples(index=False):
        if t.significativo:
            sig_si.add((t.mop, t.m, t.N, t.rival))

    combos = sorted({(r["mop"], r["m"], r["N"]) for r in sub})
    columnas = pd.MultiIndex.from_tuples(
        [(c, "") for c in _BASE]
        + [(mo, campo) for mo in moeas for campo in _CAMPOS])

    filas = []
    for (mop, m, n_pob) in combos:
        fila = [mop, m, n_pob]
        for mo in moeas:
            celda = stats.get((mop, m, n_pob, mo))
            if celda is None:            # celda faltante -> render N/A
                fila += [float("nan"), float("nan"), pd.NA, pd.NA]
            else:
                fila += [celda["media"], celda["desv"], celda["rank"],
                         (mop, m, n_pob, mo) in sig_si]
        filas.append(fila)

    df = pd.DataFrame(filas, columns=columnas)
    for mo in moeas:                     # rank como entero anulable (no '1.0')
        df[(mo, "rank")] = df[(mo, "rank")].astype("Int64")
    return df


def _celda_latex(fila, moea: str) -> str:
    """Una celda al formato del R: gris 0.5/0.8 al 1./2. lugar, '\\#' si sig."""
    rank = fila[(moea, "rank")]
    if pd.isna(rank):
        return " & N/A"
    rank = int(rank)
    sig = fila[(moea, "sig")]
    marca = "\\#" if (rank != 1 and not pd.isna(sig) and bool(sig)) else ""
    media, desv = fila[(moea, "media")], fila[(moea, "desv")]
    cuerpo = f"\\specialcell{{{media:.3e}$^{{{rank}}}${marca} \\\\ ({desv:.3e})}}"
    if rank == 1:                        # el ganador nunca lleva '\#' (como el R)
        return " & \\cellcolor[gray]{0.5} " + cuerpo
    if rank == 2:
        return " & \\cellcolor[gray]{0.8} " + cuerpo
    return " & " + cuerpo


def a_latex_doc(estructurada: pd.DataFrame, ind_id: str,
                caption: str, label: str) -> str:
    r"""
    Render LaTeX con el MISMO formato del createIndicatorTable.R, extendido a
    columnas MOP | m | N | <MOEAs...> (el R tenia MOP + dim): %.3e en media y
    desviacion, superindice = rank, `\#` si el ganador vence con significancia
    a esa celda, `N/A` si no hay datos. Bloques por MOP con \multirow (m va en
    \multirow porque es constante dentro del MOP; se agrupa por (MOP, m) para
    cubrir tambien el caso general), \cline entre filas del mismo MOP y
    \hline\hline entre MOPs. `\caption`/`\label` van antes de \end{table}
    (el R no los emitia; se agregan por conveniencia).
    """
    meta = indicators.CATALOGO[ind_id]   # valida el id; direccion desde el catalogo
    moeas = _moeas_de(estructurada)
    ncols = len(_BASE) + len(moeas)

    L = [f"% Tabla de desempeno: {meta.nombre} (sentido: {meta.sentido})",
         "\\begin{table}",
         "\\begin{tabular}{|c|c|c|" + "c|" * len(moeas) + "}",
         "\\hline",
         "{\\bf MOP} & {\\bf m} & {\\bf N}"
         + "".join(" & {\\bf " + _esc(mo) + "}" for mo in moeas) + " \\\\",
         "\\hline"]

    # Bloques de filas consecutivas con el mismo (MOP, m); la tabla ya viene
    # ordenada por (MOP, m, N), asi que cada bloque es contiguo.
    bloques: list[tuple[tuple, list]] = []
    for _, fila in estructurada.iterrows():
        clave = (fila[("MOP", "")], fila[("m", "")])
        if bloques and bloques[-1][0] == clave:
            bloques[-1][1].append(fila)
        else:
            bloques.append((clave, [fila]))

    for (mop, m), filas_bloque in bloques:
        k = len(filas_bloque)
        for j, fila in enumerate(filas_bloque):
            if j == 0:
                pref = (f"\\multirow{{{k}}}{{*}}{{{_esc(mop)}}}"
                        f" & \\multirow{{{k}}}{{*}}{{{m}}} & {fila[('N', '')]}")
            else:
                pref = f"& & {fila[('N', '')]}"
            celdas = "".join(_celda_latex(fila, mo) for mo in moeas)
            L.append(f"{pref}{celdas} \\\\ \\cline{{3-{ncols}}}")
        L.append("\\hline")              # doble \hline tras cada MOP, como el R
        L.append("\\hline")

    L += ["\\hline", "\\end{tabular}",
          f"\\caption{{{caption}}}", f"\\label{{{label}}}",
          "\\end{table}"]
    return "\n".join(L)


def a_csv_doc(estructurada: pd.DataFrame) -> bytes:
    """
    CSV largo/tidy (bytes utf-8) para descargar: una fila por celda con
    columnas MOP, m, N, MOEA, media, desv, rank, sig. Las celdas faltantes
    conservan su fila con los campos vacios.
    """
    moeas = _moeas_de(estructurada)
    filas = []
    for _, fila in estructurada.iterrows():
        for mo in moeas:
            filas.append({
                "MOP": fila[("MOP", "")], "m": fila[("m", "")],
                "N": fila[("N", "")], "MOEA": mo,
                "media": fila[(mo, "media")], "desv": fila[(mo, "desv")],
                "rank": fila[(mo, "rank")], "sig": fila[(mo, "sig")],
            })
    df = pd.DataFrame(filas, columns=["MOP", "m", "N", "MOEA",
                                      "media", "desv", "rank", "sig"])
    df["rank"] = df["rank"].astype("Int64")
    return df.to_csv(index=False).encode("utf-8")


def df_a_markdown(df: pd.DataFrame) -> str:
    """
    Tabla pipe de Markdown de un DataFrame PLANO (sin indice), construida a
    mano: el to_markdown de pandas requiere el paquete `tabulate` y esa
    dependencia no se quiere en el proyecto.
    """
    cols = [str(c) for c in df.columns]
    L = ["| " + " | ".join(cols) + " |",
         "| " + " | ".join("---" for _ in cols) + " |"]
    for _, fila in df.iterrows():
        L.append("| " + " | ".join(str(v) for v in fila) + " |")
    return "\n".join(L)


def a_markdown_doc(estructurada: pd.DataFrame) -> bytes:
    """
    Markdown (bytes utf-8) de la tabla de desempeno: mismas columnas que la
    vista de la UI (MOP, m, N + una por MOEA con "media (desv)", o N/A si
    falta el dato). La mejor media de cada fila va en **negritas**: es el
    rank 1 de la tabla estructurada, que ya respeta el sentido max/min del
    indicador (mismo criterio que el sombreado del render LaTeX).
    """
    moeas = _moeas_de(estructurada)
    display, mask = tabla_display(estructurada, moeas)
    for mo in moeas:
        display[mo] = [f"**{valor}**" if marcado else valor
                       for valor, marcado in zip(display[mo], mask[mo])]
    return df_a_markdown(display).encode("utf-8")


def tabla_display(est: pd.DataFrame,
                  moeas: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    PURA (sin streamlit; testeable): aplana la tabla estructurada de
    `tabla_estructurada` a un DataFrame de presentacion + su mascara.

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
