# moeas-BenchMarkApp

Aplicacion en **Streamlit** para **evaluar y visualizar** aproximaciones al
frente de Pareto (PFA) generadas por algoritmos evolutivos multiobjetivo
(MOEAs). La app **no ejecuta MOEAs**: parte de archivos `.pof` ya generados,
calcula indicadores de calidad, aplica estadistica y produce tablas y figuras
listas para publicar. Estancia Verano Delfin - CICESE.

## Estado funcional

- **Ingesta** de PFAs desde un `.zip` (carpetas por MOEA) o `.pof` sueltos, con
  validacion cruzada nombre/cabecera/contenido; un archivo invalido se omite y
  se reporta, sin abortar el lote.
- **Frentes de referencia** automaticos (`MOEA-visualization-main/data/`) o
  subidos por el usuario (`.zip`), con el mapeo VNT2->VIE2 / VNT3->VIE3.
- **Indicadores calculados (5)**: HV, IGD, IGD+, Epsilon+ y Delta p (via pymoo
  y numpy). **Pendientes** (a la espera de parametros del asesor): R2, Riesz
  s-energy y SPD.
- **Estadistica**: media/desviacion por escenario, corrida mediana, Mann-Whitney
  U de una cola hacia el ganador, ranking al estilo del script R del asesor,
  rangos promedio y distancia critica de Nemenyi.
- **Figuras (7)**, construidas headless con el estilo de los scripts del asesor:
  dispersion 2D y 3D, coordenadas paralelas, radar, burbuja, heatmap y
  Critical Differences plot.
- **Exportacion**: tablas en CSV / LaTeX / Markdown; figuras en PNG / SVG / EPS /
  TeX (PGF); y valores por corrida en el arbol de archivos que consume el
  script R del asesor (`domain/exportar_r.py`).
- **Flujo con step gating**: cada paso se desbloquea al completar el anterior.
- **Persistencia de sesion**: guardar/cargar el proyecto como snapshot
  `.sqlite` (datos, seleccion y resultados, sin re-evaluar).

## Flujo de trabajo

1. **Datos** — subir PFAs (y opcionalmente frentes de referencia), revisar el
   mapeo `(MOEA, MOP, m, N, corrida)` y confirmar.
2. **Indicadores** — elegir indicadores y parametros; evaluar.
3. **Resultados** — una tabla por indicador (mejor media resaltada), pruebas de
   significancia por escenario, Critical Differences plot y descargas.
4. **Visualizacion** — graficar el frente de la corrida MEDIANA del indicador
   elegido (o una corrida manual si aun no se evalua) y descargar la figura.

## Arquitectura

Tres capas con dependencia en un solo sentido:

```
ui (Streamlit)  ->  domain (logica, headless)  ->  data (I/O, persistencia)
```

- **Nada por debajo de `ui/` importa Streamlit**: figuras y tablas se
  construyen headless en `domain` (matplotlib backend Agg) y la UI solo las
  muestra/descarga.
- La UI no importa `data`: todo pasa por la fachada `domain/services.py`.
- `st.session_state` es la unica fuente de verdad de la UI.

### Estructura de carpetas

```
app.py                 # entrada delgada: config + estado + despacho del paso
ui/                    # PRESENTACION (unica capa que importa Streamlit)
  state.py             #   session_state + step gating
  sidebar.py           #   proyecto (guardar/cargar .sqlite) + navegacion
  components.py        #   stepper, placeholders de estado vacio, descargas
  steps/               #   un modulo render() por paso
    paso_datos.py
    paso_indicadores.py
    paso_resultados.py
    paso_visualizacion.py
domain/                # LOGICA (sin Streamlit)
  model.py             #   dataclasses (PFA, ConfigCSV, MapeoArchivo, Proyecto)
  indicators.py        #   catalogo + calculo (HV/IGD/IGD+/Eps+/Dp; R2/Riesz/SPD pendientes)
  preprocessing.py     #   no dominadas, duplicados, ideal-nadir, normalizar
  evaluacion.py        #   motor: indicadores por corrida, agrupados por escenario
  statistics.py        #   resumen, mediana, Mann-Whitney, ranking, Nemenyi (CD)
  tables.py            #   tabla por indicador + export CSV/LaTeX/Markdown
  figures.py           #   motor unico de figuras + export PNG/SVG/EPS/TeX
  exportar_r.py        #   valores por corrida en el formato del script R del asesor
  services.py          #   fachada hacia 'data' (la UI no importa 'data')
data/                  # DATOS (sin Streamlit)
  csv_io.py            #   lector .pof (disco/zip) + frentes de referencia
  persistence.py       #   snapshot de sesion en SQLite (guardar/cargar)
tests/                 # suite de pytest (127 pruebas)
CreateIndicator/       # createIndicatorTable.R del asesor (fuente de verdad de la tabla)
MOEA-visualization-main/  # frentes de referencia + scripts de graficado del asesor
data_ejemplo/          # .pof de muestra
```

## Convencion de nombres de archivo

```
{MOEA}_{MOP}_{m:02d}D_N{pob}_R{corrida}.pof     ej. NSGAII_DTLZ2_02D_N100_R23.pof
```

- `MOEA`: algoritmo que genero el frente (NSGAII, MOEAD, ...).
- `MOP`: problema de prueba (DTLZ2, WFG3, ...).
- `{m:02d}D`: numero de objetivos, con dos digitos (02D, 03D, ...).
- `N{pob}`: tamano de poblacion.
- `R{corrida}`: numero de corrida (estandar de literatura: 30 corridas por par
  MOEA-MOP; minimo recomendado: 5).

Un **escenario** es la tripleta `(MOP, m, N)`: todas sus corridas comparten
frente de referencia y punto de referencia de HV, y las tablas y pruebas
agrupan por escenario. Contenido del `.pof`: cabecera opcional `# N m` y un
punto por linea (m columnas separadas por espacios; se validan N y m contra el
nombre y la cabecera).

## Instalacion y ejecucion

Requiere **Python 3.10+** (el codigo usa `X | None`, `list[str]`).

```bash
python -m venv .venv
.venv\Scripts\activate           # Windows (Linux/mac: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py             # o bien: python -m streamlit run app.py
```

Opcional: la descarga de figuras en `.tex` usa el backend PGF de matplotlib y
necesita una instalacion de LaTeX en el sistema (p. ej. MiKTeX); sin LaTeX la
app deshabilita ese formato por si sola.

Tests:

```bash
python -m pytest tests/ -q
```

## Extensibilidad

- Nuevo **indicador** -> una entrada en `domain/indicators.py:CATALOGO` + su
  rama en `calcular()`.
- Nuevo **metodo de visualizacion** -> su funcion en `domain/figures.py` (y su
  entrada en `METODOS`; si aplica a m>3, tambien en `_FIGURAS_M4`).
- Nuevo **formato de exportacion de figura** -> ampliar `guardar_figura()`.


## Abrir Aplicación desde máquina Ubuntu

Ejecutar en Terminal las siguientes lineas (Previamente Instalada)

cd moeas-BenchMarkApp
source .venv/bin/activate
streamlit run app.py