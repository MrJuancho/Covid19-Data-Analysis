# Research: Capa Gold de Analítica y Agregaciones Epidemiológicas

**Feature**: `002-covid-gold` | **Spec**: [specs/002-covid-gold/spec.md](./spec.md)

El Technical Context de `plan.md` no contiene marcadores `NEEDS CLARIFICATION`: lenguaje,
dependencias, almacenamiento y objetivos de rendimiento ya están fijados por la Constitución
y por las decisiones tomadas en `001-covid-etl` (capa Silver, ya implementada). Este documento
registra las decisiones de diseño específicas de la capa Gold que sí requerían evaluar
alternativas.

---

## 1. Motor de agregación tabular

- **Decision**: Usar `pandas` (`groupby`, `pivot_table`, `resample`) sobre el DataFrame Silver
  cargado en memoria desde `data/silver/casos_unificados.parquet`.
- **Rationale**: El dataset Silver es de tamaño hospitalario local (no big data); `pandas` ya
  es dependencia del proyecto (capas Bronze/Silver) y cumple el objetivo de rendimiento
  SC-003 (< 5s) sin introducir un motor adicional (Spark, DuckDB, Polars). Mantener un único
  motor tabular en todo el pipeline simplifica el Guantelete (`mypy --strict`, fixtures).
- **Alternatives considered**:
  - `duckdb` sobre Parquet directo: más rápido en teoría, pero añade una dependencia nueva y
    un dialecto SQL paralelo a los modelos Pydantic existentes, sin beneficio medible al no
    haber restricción de memoria.
  - `polars`: mejor rendimiento en datasets grandes, pero rompe la convención de tipado ya
    validada con `pandas-stubs` en `001-covid-etl` y obligaría a reescribir utilidades de
    fechas compartidas.

## 2. Rangos etarios canónicos

- **Decision**: Implementar la binning como `pandas.cut` con bordes explícitos derivados de
  los 14 códigos de FR-002, mapeando el sentinel `-1.0` (o `NaN`) a `SIN_DATO` antes del corte
  para evitar que `pandas.cut` lo asigne a un bin numérico incorrecto.
- **Rationale**: `pandas.cut` es determinista, vectorizado y ya se usa en `cleaning/demografia.py`
  de la capa Silver (Principio II: reutilizar patrones establecidos por capa).
- **Alternatives considered**: Función `apply` fila a fila con `if/elif` — descartada por ser
  ~10-50x más lenta en datasets de miles de filas y por duplicar lógica que `pandas.cut`
  resuelve de forma nativa.

## 3. Series temporales continuas y medias móviles

- **Decision**: Construir el índice continuo con `pd.date_range(min, max, freq="D")`,
  reindexar los conteos diarios contra ese índice (`fill_value=0`), y calcular la media móvil
  con `.rolling(window=7, min_periods=1).mean()`.
- **Rationale**: `min_periods=1` garantiza que los primeros días del rango (con menos de 7
  observaciones previas) no produzcan `NaN`, cumpliendo FR-004 sin necesidad de lógica de
  relleno adicional. `reindex(fill_value=0)` resuelve el edge case "días sin actividad" del
  spec de forma nativa.
- **Alternatives considered**: Media móvil centrada (`center=True`) — descartada porque
  introduce look-ahead (usa datos futuros no disponibles en tiempo real) y no es el estándar
  para curvas epidemiológicas retrospectivas.

## 4. Cálculo seguro de tasas (división por cero)

- **Decision**: Centralizar una función `tasa_segura(numerador, denominador) -> float` en
  `analytics/_shared.py` que retorna `0.0` cuando `denominador == 0`, reutilizada por
  `demografia.py`, `series_tiempo.py`, `geografia.py` y `engine.py`. El mismo módulo aloja la
  excepción tipada `GoldIntegrityError` usada por el validador de consistencia marginal
  (ver decisión 6).
- **Rationale**: FR-003, FR-005 y los edge cases del spec exigen el mismo comportamiento
  (`0.0` determinista, nunca `NaN`/`Inf`) en cuatro módulos distintos; una única función
  evita divergencias y facilita cubrir el caso con un solo test parametrizado.
- **Alternatives considered**: `np.errstate(divide="ignore")` + reemplazo posterior de
  `inf`/`nan` — descartado por ser más difícil de tipar en modo `mypy --strict` y por ocultar
  silenciosamente errores aritméticos no relacionados con división por cero.

## 5. Persistencia y formato de salida

- **Decision**: Persistir cada tabla Gold con `DataFrame.to_parquet(..., engine="pyarrow",
  compression="snappy")`, y el resumen ejecutivo con `json.dumps(..., ensure_ascii=False,
  indent=2)` vía `pathlib.Path.write_text`.
- **Rationale**: Consistente con el contrato Silver (mismo engine/compresión) y con FR-006;
  mantiene un único formato binario en todo el pipeline para lectores externos (GIS, BI).
- **Alternatives considered**: CSV para `resumen_ejecutivo` — descartado porque el resumen es
  jerárquico (KPIs + metadatos), no tabular, y JSON es el formato natural para consumo desde
  dashboards web.

## 6. Validación de integridad estadística (SC-002 / FR-007)

- **Decision**: Añadir un validador `verificar_consistencia_marginal(df_silver, tablas_gold)`
  ejecutado al final de `generar_capa_gold(...)`, que compara `len(df_silver)` contra la suma
  de `total_casos` en `metricas_demografia` y contra la suma de conteos diarios en
  `series_temporales`, lanzando `GoldIntegrityError` (definida en `analytics/_shared.py`) si
  difieren. La CLI en `engine.py` DEBE capturar esta excepción y mapearla al código de salida
  `2` (ver `contracts/analytics_cli.md`); un `FileNotFoundError` o error de esquema al leer
  `data/silver/casos_unificados.parquet` (FR-001) se mapea al código de salida `1`.
- **Rationale**: El spec exige coincidencia aritmética exacta (SC-002) como criterio de
  "terminado"; una función de validación explícita y testeada es más auditable que confiar en
  la corrección implícita de cada agregación por separado.
- **Alternatives considered**: Verificación solo mediante tests unitarios sin guardia en
  tiempo de ejecución — descartada porque el Principio III exige que el pipeline falle de
  forma segura (código de salida `2`, ver `contracts/analytics_cli.md`) ante datos Silver que
  violen el contrato de entrada.

---

## Resultado

Todos los `NEEDS CLARIFICATION` quedan resueltos. No se requieren decisiones adicionales de
investigación antes de proceder a la implementación guiada por `tasks.md`.
