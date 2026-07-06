# -*- coding: utf-8 -*-
"""
Tests de domain/exportar_r.py: escribe los valores por corrida en el arbol/formato
EXACTO que lee CreateIndicator/createIndicatorTable.R.
"""
from __future__ import annotations

from domain import exportar_r


def _res(mop, m, N, moea, indicador, valores) -> dict:
    """Un registro con la MISMA forma que produce evaluacion.evaluar."""
    return {"mop": mop, "m": m, "N": N, "moea": moea,
            "indicador": indicador, "valores": list(valores)}


def test_exportar_estructura_ruta_y_una_linea_por_corrida(tmp_path):
    # 2 MOEAs, MISMO (MOP, m, N), varias corridas.
    resultados = [
        _res("DTLZ2", 2, 11, "NSGAII", "HV", [0.10, 0.20, 0.30]),
        _res("DTLZ2", 2, 11, "MOEAD", "HV", [0.40, 0.50, 0.60]),
    ]
    exportar_r.exportar(resultados, tmp_path)

    # Ruta: {MOEA}/N{n}/{MOEA}_{MOP}_{m:02d}D.{ext}
    f = tmp_path / "NSGAII" / "N11" / "NSGAII_DTLZ2_02D.HV"
    assert f.is_file()
    lineas = f.read_text(encoding="utf-8").splitlines()
    assert len(lineas) == 3                                  # una por corrida, SIN cabecera
    assert [float(x) for x in lineas] == [0.10, 0.20, 0.30]

    assert (tmp_path / "MOEAD" / "N11" / "MOEAD_DTLZ2_02D.HV").is_file()


def test_exportar_mapea_vnt2_a_vie2_y_token_igdplus(tmp_path):
    resultados = [_res("VNT2", 3, 15, "NSGAII", "IGD+", [1.0, 2.0])]
    exportar_r.exportar(resultados, tmp_path)

    # VNT2 -> VIE2 en el nombre; IGD+ -> token de archivo IGDplus.
    f = tmp_path / "NSGAII" / "N15" / "NSGAII_VIE2_03D.IGDplus"
    assert f.is_file()
    assert [float(x) for x in f.read_text(encoding="utf-8").split()] == [1.0, 2.0]

    # No debe existir ninguna variante con el token VNT2 ni con el '+'.
    assert not (tmp_path / "NSGAII" / "N15" / "NSGAII_VNT2_03D.IGDplus").exists()


def test_exportar_omite_grupo_sin_valores_sin_abortar(tmp_path):
    resultados = [
        _res("DTLZ2", 2, 11, "NSGAII", "HV", []),            # sin valores -> se omite
        _res("DTLZ2", 2, 11, "MOEAD", "HV", [0.5]),
    ]
    manifiesto = exportar_r.exportar(resultados, tmp_path)

    assert not (tmp_path / "NSGAII").exists()                # no se creo la carpeta del grupo vacio
    assert (tmp_path / "MOEAD" / "N11" / "MOEAD_DTLZ2_02D.HV").is_file()
    assert set(manifiesto) == {"HV"}


def test_manifiesto_must_maximize(tmp_path):
    resultados = [
        _res("DTLZ2", 2, 11, "NSGAII", "HV", [0.1]),
        _res("DTLZ2", 2, 11, "NSGAII", "IGD", [0.2]),
    ]
    manifiesto = exportar_r.exportar(resultados, tmp_path)

    assert manifiesto["HV"]["MUST_MAXIMIZE"] == 1            # HV es 'max'
    assert manifiesto["IGD"]["MUST_MAXIMIZE"] == 0          # IGD es 'min'
    assert manifiesto["HV"]["token"] == "HV"
