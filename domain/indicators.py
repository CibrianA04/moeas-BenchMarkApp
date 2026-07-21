# -*- coding: utf-8 -*-
"""
Indicadores de calidad: catalogo + calculo. HV, IGD, IGD+, Eps+ y Dp se
calculan (pymoo / numpy); R2, Riesz y SPD siguen pendientes de los parametros
lanzan NotImplementedError.

Pareto-compliance es un atributo de Primera clase: solo los indicadores
compliant (estricta/debil) permiten conclusiones fuertes. HV e IGD+ lo son;
IGD, GD, MS no.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import preprocessing


@dataclass(frozen=True)
class MetaIndicador:
    id: str
    nombre: str          # texto para mostrar en la UI
    sentido: str         # "max" (mayor mejor) | "min" (menor mejor)
    requiere_ref: bool   # necesita frente de referencia
    compliance: str      # "estricta" | "debil" | "no"
    grupo: str           # "principal" | "secundario"
    descripcion: str = ""


# Catalogo. Punto de EXTENSION: agregar un indicador = una entrada aqui + su
# rama en calcular().
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
             ref: np.ndarray | None = None,
             punto_ref: np.ndarray | None = None, **params) -> float:
    """
    Calcula UN indicador sobre un PFA.

    - Valida `requiere_ref` contra el CATALOGO: si el indicador necesita frente de
      referencia , lanza ValueError.
    - HV: via pymoo. Usa `punto_ref` (punto de referencia/nadir); si es None, se
      toma el nadir del propio conjunto 
    - IGD, IGD+ y Dp: via pymoo . Eps+ (epsilon aditivo)
      se calcula con numpy (version de pymoo no trae el modulo de epsilon).
      Los cuatro usan el frente de referencia `ref` ya validado arriba.
    - Dp acepta el parametro `p` (default 2?) PENDIENTE de implementar
    - R2/Riesz/SPD aun NO estan implementados: lanzan NotImplementedError.
    """
    if ind_id not in CATALOGO:
        raise KeyError(f"Indicador desconocido: '{ind_id}'.")
    meta = CATALOGO[ind_id]
    if meta.requiere_ref and ref is None:
        raise ValueError(
            f"El indicador '{ind_id}' requiere un frente de referencia (ref)."
        )

    if ind_id == "HV":
        if punto_ref is None:
            _, punto_ref = preprocessing.estimar_ideal_nadir(np.asarray(puntos, float))
        return _hv_pymoo(puntos, punto_ref)

    if ind_id == "IGD":
        from pymoo.indicators.igd import IGD   # import 
        return float(IGD(np.asarray(ref, float))(np.asarray(puntos, float)))

    if ind_id == "IGD+":
        from pymoo.indicators.igd_plus import IGDPlus   # import
        return float(IGDPlus(np.asarray(ref, float))(np.asarray(puntos, float)))

    if ind_id == "Eps+":
        # Epsilon ADITIVO por numpy: esta version de pymoo (0.6.1.x) no incluye el
        # modulo pymoo.indicators.epsilon. 
        return _eps_plus_aditivo(puntos, ref)

    if ind_id == "Dp":
        # Delta_p = max(GD_p, IGD_p). `p` se expone (default 2) como CONVENCION
        # PENDIENTE de implementar. OJO: los GD/IGD
        # de esta version de pymoo promedian distancias (equivale a p=1) y NO exponen
        # el exponente p; por eso hoy `p` NO se propaga al computo (queda como TODO
        # hasta fijar la convencion exacta de Delta_p
        p = params.get("p", 2)  # noqa: F841  (inerte hasta fijar la convencion; ver arriba)
        from pymoo.indicators.gd import GD    # import
        from pymoo.indicators.igd import IGD  # import
        R = np.asarray(ref, float)
        P = np.asarray(puntos, float)
        return max(float(GD(R)(P)), float(IGD(R)(P)))

    raise NotImplementedError(
        f"El computo de '{ind_id}' aun no esta implementado."
    )


def preparar_indicadores(ids, ref) -> dict:
    """
    Evaluadores REUSABLES para un escenario: {ind_id: callable(P) -> float}.

    Los indicadores basados en referencia construian IGD(ref)/GD(ref) POR
    CORRIDA, re-procesando el frente (~10k puntos) cada vez. Aqui se construyen
    UNA vez por escenario y se reusan entre corridas; "Dp" comparte el MISMO
    objeto IGD que "IGD" (antes lo recalculaba). `calcular()` sigue siendo la
    via por-llamada (tests, usos sueltos); el MOTOR (evaluacion.evaluar) usa esta.
    Cubre: IGD, IGD+, Eps+, Dp. HV NO entra: su punto de referencia depende
    de la union del escenario y lo maneja el motor via calcular().
    Ids no cubiertos (p. ej. R2, pendiente de convencion) caen a calcular()
      DENTRO del callable: el error se lanza por corrida, preservando la
      semantica de `omitidos` del motor.
    """
    if ref is None:
        raise ValueError("preparar_indicadores requiere un frente de referencia.")
    R = np.asarray(ref, dtype=float)

    igd_obj = None
    if "IGD" in ids or "Dp" in ids:
        from pymoo.indicators.igd import IGD                # import perezoso
        igd_obj = IGD(R)

    evaluadores: dict = {}
    for ind_id in ids:
        if ind_id == "IGD":
            evaluadores[ind_id] = (
                lambda P, _igd=igd_obj: float(_igd(np.asarray(P, dtype=float))))
        elif ind_id == "IGD+":
            from pymoo.indicators.igd_plus import IGDPlus   # import perezoso
            igdp = IGDPlus(R)
            evaluadores[ind_id] = (
                lambda P, _igdp=igdp: float(_igdp(np.asarray(P, dtype=float))))
        elif ind_id == "Eps+":
            evaluadores[ind_id] = lambda P, _R=R: _eps_plus_aditivo(P, _R)
        elif ind_id == "Dp":
            from pymoo.indicators.gd import GD              # import perezoso
            gd = GD(R)
            evaluadores[ind_id] = (
                lambda P, _gd=gd, _igd=igd_obj: max(
                    float(_gd(np.asarray(P, dtype=float))),
                    float(_igd(np.asarray(P, dtype=float)))))
        else:
            evaluadores[ind_id] = lambda P, _i=ind_id: calcular(_i, P, ref=R)
    return evaluadores


def _hv_pymoo(puntos: np.ndarray, punto_ref: np.ndarray) -> float:
    """
    Hypervolume via pymoo (minimizacion). `punto_ref` debe dominar (ser >= en cada
    objetivo) a todos los puntos para que el HV sea > 0. Import: solo se
    necesita pymoo cuando de verdad se calcula HV.
    """
    from pymoo.indicators.hv import HV   # import perezoso (dependencia opcional)

    P = np.asarray(puntos, dtype=float)
    ref = np.asarray(punto_ref, dtype=float)
    return float(HV(ref_point=ref)(P))


def _eps_plus_aditivo(puntos: np.ndarray, ref: np.ndarray) -> float:
    """
    Indicador epsilon ADITIVO unario I_eps+(A, R) para MINIMIZACION, calculado con
    numpy porque esta version de pymoo (0.6.1.x) no trae `pymoo.indicators.epsilon`.

        I_eps+ = max_{r in R} min_{a in A} max_i (a_i - r_i)

    Es el minimo desplazamiento aditivo eps tal que cada punto r del frente de
    referencia R queda (debilmente) eps-dominado por algun punto a del PFA A
    (a_i - eps <= r_i para todo objetivo i). Puede ser negativo si A cubre a R con
    holgura. Menor es mejor; 0 si A cubre exactamente a R.
    """
    A = np.asarray(puntos, dtype=float)
    R = np.asarray(ref, dtype=float)
    # diff[a, r, i] = A[a, i] - R[r, i]
    diff = A[:, None, :] - R[None, :, :]
    por_objetivo = diff.max(axis=2)     # eps que cada a necesita para eps-dominar cada r
    por_ref = por_objetivo.min(axis=0)  # mejor a para cubrir cada r
    return float(por_ref.max())         # peor r
