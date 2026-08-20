# Contrato de Interfaz: `src/covid_analytics/ui/filtros.py`

Módulo interno de lógica pura (sin dependencia de `streamlit`), consumido por `ui/app.py` y
probado directamente con `pytest` (sin `AppTest`). Implementa las reglas de filtrado resueltas en
`/speckit-clarify` (ver `## Clarifications` en `spec.md`).

## Tipos

```text
FiltroTablero:
    fecha_inicio: date
    fecha_fin: date
    sexos: list[Literal["M", "F"]]           # vacío = sin filtro
    grupos_edad_ui: list[Literal["<18","18-39","40-59","60+"]]  # vacío = sin filtro
    derechohabiencias: list[Literal["IMSS","ISSSTE","ISSEMYM","INSABI","PRIVADO","NINGUNA"]]  # vacío = sin filtro

VistaKPI:
    total_pruebas: int
    casos_positivos_confirmados: int
    tasa_global_positividad: float
    tasa_hospitalizacion: float
```

## Funciones expuestas

| Función | Firma | Contrato |
|---|---|---|
| `aplicar_filtro_series` | `(df: pd.DataFrame, filtro: FiltroTablero) -> pd.DataFrame` | Recorta `df` (salida de `cargar_series_temporales`) al rango `[fecha_inicio, fecha_fin]` inclusive por columna `fecha`. Ignora `sexos`/`grupos_edad_ui`/`derechohabiencias` (la tabla no tiene esas dimensiones). |
| `aplicar_filtro_demografia` | `(df: pd.DataFrame, filtro: FiltroTablero) -> pd.DataFrame` | Filtra `df` (salida de `cargar_metricas_demografia`) por `sexo` y `grupo_edad_ui` con **coincidencia exacta** (FR-004): lista vacía ⟹ sin filtrar esa dimensión (incluye `OTRO`/`INDETERMINADO`/`SIN_DATO`); lista no vacía ⟹ solo esos valores. |
| `aplicar_filtro_derechohabiencia` | `(df: pd.DataFrame, filtro: FiltroTablero) -> pd.DataFrame` | Filtra `df` (salida de `cargar_metricas_derechohabiencia`) por `derechohabiencia`, misma semántica de coincidencia exacta que arriba (`OTRA` se incluye solo cuando la lista está vacía). |
| `calcular_vista_kpi` | `(kpis_df: pd.DataFrame, series_filtrada: pd.DataFrame) -> VistaKPI` | Si `filtro` no acota sexo/edad/derechohabiencia (todas las listas vacías) y el rango de fechas cubre el 100% de `series_temporales`, retorna los valores tal cual de `kpis_generales.parquet` (sin recomputar). En caso contrario, recalcula `total_pruebas`/`casos_positivos_confirmados`/tasas a partir de `series_filtrada` (columnas ya agregadas por día, sin tocar microdatos). |
| `dataframe_vacio_tras_filtro` | `(df: pd.DataFrame) -> bool` | `True` si `df` tiene 0 filas tras aplicar cualquiera de los filtros anteriores — usado por `app.py` para decidir el estado "sin datos para esta selección" (FR-013). |

## Garantías

1. **Pureza**: ninguna función de este módulo importa `streamlit` ni tiene efectos secundarios
   (no escribe a disco, no llama `st.*`) — 100% testeable con `pytest` puro.
2. **Determinismo**: dado el mismo `df` y `filtro`, el resultado es idéntico en cualquier
   invocación (sin aleatoriedad, sin dependencia de estado global).
3. **Sin transformaciones pesadas**: todas las operaciones son filtrado/selección sobre
   DataFrames ya agregados por Gold (cientos de filas, no microdatos) — ninguna función reagrupa
   datos crudos ni reimplementa lógica de `analytics/`.
4. **Deselección total = sin filtro**: una lista vacía en cualquier campo de `FiltroTablero`
   NUNCA produce cero resultados por sí sola; se interpreta como "todas las categorías" (Edge
   Case de spec.md).
