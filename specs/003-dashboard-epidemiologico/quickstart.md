# Quickstart: Dashboard Epidemiológico Interactivo (Streamlit)

**Feature**: `003-dashboard-epidemiologico` | **Spec**: [specs/003-dashboard-epidemiologico/spec.md](./spec.md)

Guía para validar de extremo a extremo que la extensión de Gold y el tablero funcionan una vez
implementados siguiendo `tasks.md`. No sustituye al Guantelete (Principio III); es la
comprobación funcional rápida de que la capa Gold extendida y la UI se generan/renderizan
correctamente.

## Prerrequisitos

1. Entorno del proyecto instalado con `uv sync` (incluye `streamlit`, `plotly`, `pyshp` una vez
   añadidos a `pyproject.toml` en Fase de implementación).
2. Dataset Silver disponible en `data/silver/casos_unificados.parquet` (001-covid-etl).
3. Módulos Gold extendidos según `tasks.md` (`grupo_edad_ui` en `demografia.py`,
   `derechohabiencia.py` nuevo, `engine.py` actualizado).
4. Módulos de UI implementados (`src/covid_analytics/ui/`).

## Validación 1 — Regenerar la capa Gold extendida

```bash
uv run python -m covid_analytics.analytics.engine \
  --silver-path data/silver/casos_unificados.parquet \
  --output-dir data/gold
```

**Resultado esperado**:
- Código de salida `0`.
- `data/gold/metricas_demografia.parquet` incluye la columna `grupo_edad_ui`.
- Se crea `data/gold/metricas_derechohabiencia.parquet` (nuevo).
- Los demás archivos (`series_temporales.parquet`, `distribucion_geografica.parquet`,
  `kpis_generales.parquet`, `resumen_ejecutivo.json`) se regeneran sin cambios de esquema.

## Validación 2 — Consistencia de la nueva dimensión (FR-005a, FR-006a)

```bash
uv run python - <<'PY'
import pandas as pd

silver = pd.read_parquet("data/silver/casos_unificados.parquet")
demografia = pd.read_parquet("data/gold/metricas_demografia.parquet")
derechohabiencia = pd.read_parquet("data/gold/metricas_derechohabiencia.parquet")

assert "grupo_edad_ui" in demografia.columns
assert demografia["total_casos"].sum() == len(silver)
assert derechohabiencia["total_casos"].sum() == len(silver)

total_positivos = int((silver["resultado_prueba"] == "POSITIVO").sum())
assert derechohabiencia.loc[derechohabiencia["resultado_prueba"] == "POSITIVO", "total_casos"].sum() == total_positivos
print("OK: extensiones Gold consistentes con Silver")
PY
```

**Resultado esperado**: `OK: extensiones Gold consistentes con Silver` sin `AssertionError`.

## Validación 3 — Lanzar el tablero

```bash
uv run streamlit run src/covid_analytics/ui/app.py
```

**Resultado esperado**: el navegador abre el tablero en `http://localhost:8501`; las 4 tarjetas
KPI y las 5 pestañas cargan sin error (ver `contracts/app_layout_contract.md` para el layout
exacto). Verificar manualmente:
- Cambiar el rango de fechas actualiza la curva y las tarjetas KPI (US1).
- Filtrar por `FEMENINO` en sexo deja solo esa barra en la pirámide y ajusta los KPIs (US2).
- El mapa de la Pestaña 3 colorea los municipios de la zona de influencia (US3).
- La Pestaña 4 muestra el cruce derechohabiencia × hospitalización/resultado (US4).
- La Pestaña 5 muestra el contenido de `data_quality_summary.json` (US5).

## Validación 4 — Estado degradado (FR-013)

```bash
mv data/gold/metricas_derechohabiencia.parquet /tmp/metricas_derechohabiencia.parquet.bak
uv run streamlit run src/covid_analytics/ui/app.py
# Verificar manualmente: solo la Pestaña 4 y el filtro de derechohabiencia muestran
# "no disponible"; el resto del tablero (KPIs, curva, demografía, mapa, calidad) funciona.
mv /tmp/metricas_derechohabiencia.parquet.bak data/gold/metricas_derechohabiencia.parquet
```

**Resultado esperado**: degradación por pestaña, sin pantalla en blanco ni traceback (Clarifications, spec.md).

## Validación 5 — Cero PII en el tablero (SC-004)

```bash
uv run python - <<'PY'
import pandas as pd

columnas_prohibidas = {"nombre", "telefono", "domicilio", "curp", "paciente_id"}
for tabla in ["metricas_demografia", "series_temporales", "distribucion_geografica", "kpis_generales", "metricas_derechohabiencia"]:
    df = pd.read_parquet(f"data/gold/{tabla}.parquet")
    assert not (set(df.columns) & columnas_prohibidas), f"PII detectado en {tabla}"
print("OK: cero columnas PII en artefactos consumidos por el tablero")
PY
```

**Resultado esperado**: `OK: cero columnas PII en artefactos consumidos por el tablero`.

## Validación 6 — El Guantelete

```bash
uv run mypy --strict src
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest --cov=src --cov-fail-under=90
```

**Resultado esperado**: los cuatro comandos terminan en verde, incluyendo
`tests/unit/test_ui_app.py` (`AppTest`) y cobertura >= 90% con los nuevos módulos de
`analytics/` y `ui/`.

## Referencias

- Esquemas de tablas: [`data-model.md`](./data-model.md)
- Contratos de datos e interfaces: [`contracts/`](./contracts/)
- Tareas de implementación: [`tasks.md`](./tasks.md)
