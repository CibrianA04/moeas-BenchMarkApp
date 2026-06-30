# CLAUDE.md — Guía del proyecto BenchMark-MOEAs

> App para **evaluar y visualizar** aproximaciones al frente de Pareto (PFA)
> generadas por algoritmos evolutivos multiobjetivo (MOEAs).
> Estancia Verano Delfín · CICESE. Esta app **no ejecuta** MOEAs: solo lee
> resultados ya generados, los evalúa y los presenta.

Toda contribución sigue dos reglas no negociables: **(1)** la arquitectura de 3
capas de abajo, y **(2)** el contrato con el script del doctor (la app **no**
reimplementa estadística ni tablas; solo **exporta** valores por corrida).

---

## 1. Arquitectura: 3 capas, dependencia en un solo sentido

```
        PRESENTACIÓN              DOMINIO                 DATOS
        ui/  (Streamlit)   ->     domain/  (headless) ->  data/  (E/S)
        lo que ve el usuario      lógica pura            archivos / SQLite
```

**Reglas duras:**

1. **Solo `ui/` importa `streamlit`.** Nada en `domain/` ni en `data/` lo importa.
   (Verificable con grep: no debe haber `import streamlit` fuera de `ui/`.)
2. **Las dependencias van solo hacia abajo:** `ui → domain → data`. Nunca al
   revés ni en diagonal. La UI **no** importa `data`: pide todo a `domain`
   (fachada en `domain/services.py`).
   - Única excepción sancionada: `data/csv_io.py` importa `domain.model` (las
     dataclasses `PFA`/`ConfigCSV` son la forma compartida que viaja entre capas).
3. **Figuras y tablas se construyen HEADLESS en el Dominio** y solo se
   **renderizan** en Presentación:
   - `domain/figures.py` usa matplotlib con backend `Agg` y devuelve objetos
     `Figure`; la UI hace `st.pyplot(fig)` y luego `figures.cerrar(fig)`.
   - `domain/tables.py` devuelve `DataFrame`/cadenas (CSV/LaTeX); la UI solo las
     muestra/ofrece a descargar.
4. **`st.session_state` es la única fuente de verdad** de la UI (ver `ui/state.py`).

---

## 2. Estructura de carpetas

```
app.py                     Punto de entrada: config + estado + despacho del paso
ui/                        PRESENTACIÓN (única capa que importa streamlit)
  state.py                   session_state + navegación entre pasos
  sidebar.py                 configuración global + navegación
  components.py              stepper, placeholders, bloque de descargas
  steps/                     un render() por paso del flujo
    paso_datos.py            Paso 1 · carga de PFA (.zip / .pof)
    paso_indicadores.py      Paso 2 · elegir indicadores
    paso_resultados.py       Paso 3 · tablas + pruebas (presentación)
    paso_visualizacion.py    Paso 4 · graficar un frente real
domain/                    DOMINIO (lógica, sin streamlit)
  model.py                   dataclasses: PFA, MapeoArchivo, ConfigCSV, Proyecto
  services.py                FACHADA hacia data/ (lo que consume la UI)
  indicators.py              catálogo de indicadores + calcular() [STUB]
  preprocessing.py           filtrado/normalización/nadir [STUBS]
  statistics.py              agregación + pruebas [STUBS]
  tables.py                  construcción/exportación de tablas [parcial/STUB]
  figures.py                 matplotlib headless (motor único de gráficas)
  mock.py                    generadores de ejemplo (DESHABILITADOS)
data/                      DATOS (sin streamlit; solo domain.model)
  csv_io.py                  lector real de .pof (disco y .zip) — HECHO
  persistence.py             proyecto en SQLite [STUB]
tests/                     pytest (de momento, el lector de .pof)
CreateIndicator/           createIndicatorTable.R — SCRIPT DEL DOCTOR (ver §5)
MOEA-visualization-main/   frentes de referencia + plots de referencia (ver §4)
data_ejemplo/              7 .pof de muestra para tests (datos, no código)
papers/                    PDFs de referencia (no código)
```

---

## 3. Estado actual (qué está HECHO y qué es STUB)

| Pieza | Estado | Dónde |
|---|---|---|
| Ingesta de `.zip` y `.pof` (lectura + validación cruzada) | **HECHO** | `data/csv_io.py`, `domain/services.py`, `ui/steps/paso_datos.py` |
| Vista previa de un PFA real + **graficado básico 2D/3D** | **HECHO** | `paso_datos.py`, `paso_visualizacion.py`, `domain/figures.py` |
| Gráfica del frente de la **MEDIANA** (la que pide el doc) | **PENDIENTE** (depende de tener el indicador calculado) | `paso_visualizacion.py` |
| Catálogo de indicadores (HV, IGD, IGD+, R2, Δp, ε+, Riesz, SPD) | **HECHO** | `domain/indicators.py` (`CATALOGO`) |
| **Cómputo** de indicadores (`calcular`) | **STUB** | `domain/indicators.py` (devuelve mock) |
| Preprocesamiento (no dominadas, nadir, normalizar) | **STUB** | `domain/preprocessing.py` |
| Estadística (Wilcoxon/Mann-Whitney/Friedman, ranking) | **STUB** | `domain/statistics.py` |
| Tablas de resultados (medias por (MOEA,MOP)) | **STUB** | `domain/tables.py` (usa `mock`) |
| Persistencia del proyecto (SQLite) | **STUB** | `data/persistence.py` |
| Frentes de referencia (carga para indicadores de distancia) | **PENDIENTE** | ver §4 |
| **Exportación** de valores por corrida para el script R | **PENDIENTE** | ver §5 |

> Nota: `domain/mock.py` está deshabilitado a propósito; las piezas STUB que aún
> lo usan (`tables.py`) mostrarán datos vacíos hasta conectarse al cómputo real.

---

## 4. Formatos de archivo

Hay **dos** tipos de `.pof`, con nombres DISTINTOS. No confundirlos.

**(a) PFA de una corrida** (lo que sube el usuario, ya implementado):
```
{MOEA}_{MOP}_{m:02d}D_N{N}_R{run}.pof      ej. NSGAII_DTLZ2_02D_N11_R23.pof
```
- Línea 1 = cabecera `# N m` (puede faltar → se salta con `comment='#'`).
- Resto: un punto por línea, m columnas separadas por espacios (con espacio
  final), decimal con punto, notación científica, valores posiblemente negativos.
- Lector: `pd.read_csv(fuente, sep=r"\s+", comment="#", header=None)`.
- Validación cruzada obligatoria: columnas reales == m(nombre) == m(cabecera);
  filas reales == N(nombre) == N(cabecera). Nunca recortar ni rellenar en silencio.

**(b) Frente de referencia** (verdad de terreno por (MOP, dimensión)):
```
MOEA-visualization-main/data/{MOP}_{dim:02d}D.pof   ej. DTLZ2_03D.pof, WFG3_03D.pof
```
- **SOLO** los archivos con el patrón EXACTO `{MOP}_{dim:02d}D.pof` (un único guion
  bajo, sin sufijos) son frentes de referencia. Sin MOEA ni corrida en el nombre.
- **NO son frentes de referencia** (son datos de demo del doc, hay que ignorarlos):
  `*_sf_*.pof`, y los prefijos `SLD_*`, `INV_SLD_*`, `LINEAR_*` (más algún `.png`).
- Lo necesitan los indicadores basados en distancia (IGD, IGD+, R2, Δp, ε+).
- Mismo formato de contenido que (a).
- **Conteo real:** de los 265 archivos del folder, solo **74 son frentes de
  referencia** verdaderos; los otros 191 son demo (SLD/INV_SLD/LINEAR/`_sf_`/`.png`).

**Cobertura para mi dataset** (¿existe el `.pof` de referencia exacto?):

| MOP | ¿Frente de referencia? | Dimensiones disponibles |
|---|---|---|
| DTLZ1 | sí | 02D–10D |
| DTLZ2 | sí | 02D–10D |
| DTLZ7 | sí | 02D–10D |
| WFG3  | sí | 02D–10D |
| IMOP3 | sí | **solo 02D** |
| IMOP7 | sí | **solo 03D** |
| IMOP8 | sí | **solo 03D** |
| VNT2  | **no directo** → vía `VIE2_03D.pof` | VIE2: 03D |
| VNT3  | **no directo** → vía `VIE3_03D.pof` | VIE3: 03D |

> `VNT2`/`VNT3` no tienen archivo propio: dependen del mapeo `VNT2→VIE2`,
> `VNT3→VIE3` (**PENDIENTE confirmar con el doc**). Para `(MOP,m)` sin frente
> exacto NO se sustituye por uno aproximado: se reporta como faltante.

El campo `n` (de `N{N}`) tiene **rol semántico pendiente de confirmar con el doc**
(¿tamaño de población o cardinalidad del frente?); ver también `card` en §5. No
asumirlo hasta confirmarlo.

---

## 5. Contrato con el doctor (createIndicatorTable.R) — FUENTE ÚNICA DE VERDAD

`CreateIndicator/createIndicatorTable.R` es la **fuente única de verdad** para:
**medias, desviación, prueba de Wilcoxon, ranking y la tabla LaTeX final**.

**La app NO reimplementa nada de eso.** El trabajo de la app es **exportar los
valores de indicador por corrida** exactamente en el formato/ruta que ese script
lee. Reimplementar medias/Wilcoxon/tablas en Python sería duplicar (y arriesgar
divergir de) la fuente de verdad del doctor.

### Qué lee el script (la ruta que la app debe producir)

```
{dirInput}/{MOEA}/{card}/{MOEA}_{MOP}_{dim:02d}D.{extension}
```
- `extension` = nombre del indicador (p. ej. `HV`, `IGD`). Se corre el script
  **una vez por indicador**.
- `card` = bucket de cardinalidad/población (6.º argumento del script y también
  un nivel de carpeta). Probablemente ligado al `N` de §4 — **pendiente confirmar**.
- Cada archivo se lee con `read.table(header=FALSE)` y el script usa la **columna
  V1**: por tanto el archivo es **una columna = un valor del indicador por corrida**
  (una fila por corrida). Sin cabecera.

### Qué hace el script (y por eso la app no lo repite)

- `mean(data$V1)` y `sd(data$V1)` por (MOEA, MOP, dim).
- Ranking: ordena MOEAs por media (descendente si `MUST_MAXIMIZE=1`, p. ej. HV/SPD;
  ascendente si no).
- **Dirección de R2 PENDIENTE:** el catálogo la marca como `min`, pero el valor
  correcto de `MUST_MAXIMIZE` para R2 está **pendiente de confirmar con el doc**
  (no fijarlo como definitivo). HV y SPD sí son `max`; IGD, IGD+, Δp, ε+ son `min`.
- Wilcoxon de una cola del ganador contra cada rival (`alternative` = `greater`
  o `less` según `MUST_MAXIMIZE`); marca `#` si `p ≤ 0.05`.
- Genera la tabla LaTeX: superíndice = ranking, sombreado gris al 1.º y 2.º,
  más un `*_avgRank.txt` con rankings para el ranking promedio / CD plot.
- Argumentos: `extension MUST_MAXIMIZE dirInput dirOutput executeWilcoxon CARD`.
- Universo de MOEAs (13) y etiquetas LaTeX están fijados dentro del script
  (`ARMOEA, AdaW, BiGE, MOEAD, MOEADD, MOMBIII, NSGAII, RPEA, SPEA2SDE, SPEAR,
  SRA, Two_Arch2, tDEA`); MOPs/DIMs se editan arriba del script.

### Implicación de diseño

El Paso 3 (Resultados) de la app es, a término, **un exportador**: produce el
árbol `dirInput/{MOEA}/{card}/{MOEA}_{MOP}_{dd}D.{IND}` con un valor por corrida,
y el doctor (o un wrapper que llame a R) genera la tabla. La tabla que se vea en
la UI debe ser consistente con la que produce R, no una segunda implementación.

---

## 6. Convenciones

- **Idioma:** comentarios y textos de UI en **español**. Identificadores de código
  en español salvo términos técnicos asentados (PFA, MOEA, MOP, HV, IGD...).
- **Una capa / un archivo por tarea:** cada módulo tiene una responsabilidad clara
  (lectura, modelo, indicadores, figuras, tablas, estadística...). Extender =
  añadir en el archivo correcto, no mezclar responsabilidades.
  - Nuevo indicador → una entrada en `indicators.CATALOGO` (+ su rama en `calcular`).
  - Nuevo método de figura → una entrada en `figures.METODOS` (+ su función).
- **Lectura por lotes tolerante:** un archivo malo se **omite y se reporta**
  (no aborta el lote). La UI muestra "X cargados, Y omitidos (motivo)".
- **Sin datos inventados** en la UI real: si no hay datos, placeholder claro, no
  números falsos.
- **Texto del código en ASCII** cuando sea posible (evita problemas de codificación
  en Windows); el contenido de cara al usuario sí lleva acentos.

---

## 7. Ejecutar y probar

```powershell
# App (Python no está en PATH en la máquina de desarrollo; usar -m streamlit):
py -m streamlit run app.py

# Tests del lector de .pof:
py -m pytest tests/ -v
```

`requirements.txt` lista las dependencias (streamlit, numpy, pandas, matplotlib,
jinja2; pytest para pruebas). `scipy`/`pymoo` están como FUTURO (cómputo real).
