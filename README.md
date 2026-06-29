# moeas-BenchMarkApp

Aplicacion para **evaluar y visualizar** aproximaciones al frente de Pareto
(PFA) generadas por algoritmos evolutivos multiobjetivo (MOEAs).
Estancia Verano Delfin - CICESE.

> **Estado actual: MAQUETA en capas (diseno, sin logica).**
> No lee datos reales ni calcula indicadores: todo lo que se ve son datos de
> ejemplo. El objetivo de esta etapa es mostrar la **arquitectura** y la
> **interfaz**.

## Arquitectura (regla dura)

Tres capas con **dependencia en un solo sentido**:

```
ui (Streamlit)  ->  domain (logica, headless)  ->  data (persistencia, I/O)
```

- **Nada por debajo de `ui/` importa Streamlit.**
- `st.session_state` es la **unica fuente de verdad**.
- **Step gating**: cada paso se desbloquea solo si se completo el anterior.

### Estructura de carpetas

```
app.py                 # entrada delgada: config + estado + despacho del paso
ui/                    # PRESENTACION (unica capa que importa Streamlit)
  state.py             #   session_state + gating
  sidebar.py           #   config global + navegacion
  steps/               #   un modulo render() por paso
    paso_datos.py
    paso_indicadores.py
    paso_resultados.py
    paso_visualizacion.py
domain/                # LOGICA (sin Streamlit; construye tablas/figuras headless)
  model.py             #   dataclasses (Proyecto, PFA, MapeoArchivo, ...)
  indicators.py        #   catalogo + calcular() [STUB] + Pareto-compliance
  preprocessing.py     #   filtrar dominadas, normalizar, nadir [STUBS]
  statistics.py        #   agregacion + pruebas por escenario [STUBS]
  tables.py            #   tabla por indicador + export CSV/LaTeX
  figures.py           #   matplotlib (motor unico, backend Agg)
  services.py          #   facade hacia 'data' (la UI no importa 'data')
  mock.py              #   generadores de datos de ejemplo
data/                  # DATOS (sin Streamlit ni domain)
  csv_io.py            #   lectura de PFA / referencias [STUBS]
  persistence.py       #   proyecto en SQLite [STUBS]
```

## Stack

UI: **Streamlit** · graficas: **matplotlib** (motor unico) · HV: **pymoo**
(interfaz lista para cambiar a binario en C) · persistencia: **SQLite**.
Exportacion: CSV, LaTeX, PNG, SVG, EPS, TikZ.

## Flujo de trabajo (pasos con gating)

1. **Datos** - cargar CSV de PFA y asociarlos a `(MOEA, MOP, corrida)`; subir
   frentes de referencia.
2. **Indicadores** - elegir indicadores (HV, IGD, IGD+, R2, Delta p, Epsilon+,
   Riesz s-energy, Solow-Polasky) y preprocesamiento.
3. **Resultados** - una tabla por indicador (mejor media resaltada), pruebas
   por escenario (Wilcoxon / Mann-Whitney / Friedman+post-hoc) y export CSV/LaTeX.
4. **Visualizacion** - graficar el frente asociado a la mediana (2D, 3D,
   coordenadas paralelas) y descargar la figura.

## Convenciones de datos

- 1 CSV = 1 PFA = una corrida: `N filas (puntos) x m columnas (objetivos)`.
- Mapeo: una linea por archivo -> `archivo = (MOEA, MOP, corrida)`.
- Una tabla **por indicador** (no se mezclan: escalas/direcciones distintas).
- Estandar: 30 corridas por par (MOEA, MOP); la app advierte si n < 5.
- Pareto-compliance es atributo de primera clase (HV, IGD+ si; IGD, GD, MS no).

## Instalacion y ejecucion

```bash
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Extensibilidad

- Nuevo **indicador** -> una entrada en `domain/indicators.py:CATALOGO` (+ su rama en `calcular`).
- Nuevo **metodo de visualizacion** -> una entrada en `domain/figures.py:METODOS` (+ su funcion).
- Nuevo **formato de figura** -> ampliar `guardar_figura()`.


