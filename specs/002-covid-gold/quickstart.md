# Quickstart: Capa Gold de Analítica y Agregaciones Epidemiológicas

**Feature**: `002-covid-gold` | **Spec**: [specs/002-covid-gold/spec.md](./spec.md)

Guía para validar de extremo a extremo que la capa Gold funciona una vez implementada
siguiendo `tasks.md`. No sustituye al Guantelete (Principio III); es la comprobación
funcional rápida de que las tablas y el resumen ejecutivo se generan correctamente.

## Prerrequisitos

1. Entorno del proyecto instalado con `uv sync` (incluye grupo `dev`).
2. Dataset Silver disponible en `data/silver/casos_unificados.parquet`, generado previamente
   por la capa `001-covid-etl`:
   ```bash
   uv run python -m covid_analytics.pipeline --layer silver
   ```
   (o el comando equivalente ya usado en `specs/001-covid-etl/quickstart.md`).
3. Módulos de la capa Gold implementados según `tasks.md` (`src/covid_analytics/analytics/`).

## Validación 1 — Ejecución del motor analítico (CLI)

Ver contrato completo en [`contracts/analytics_cli.md`](./contracts/analytics_cli.md).

```bash
uv run python -m covid_analytics.analytics.engine \
  --silver-path data/silver/casos_unificados.parquet \
  --output-dir data/gold
```

**Resultado esperado**:
- Código de salida `0`.
- Se crean en `data/gold/`: `metricas_demografia.parquet`, `series_temporales.parquet`,
  `distribucion_geografica.parquet`, `kpis_generales.parquet`, `resumen_ejecutivo.json`.
- Tiempo total de ejecución < 5 segundos (SC-003), verificable con `time`:
  ```bash
  time uv run python -m covid_analytics.analytics.engine --silver-path data/silver/casos_unificados.parquet --output-dir data/gold
  ```

## Validación 2 — Pipeline end-to-end (Bronze → Silver → Gold)

```bash
uv run python -m covid_analytics.pipeline --layer gold
```

**Resultado esperado**: mismo resultado que la Validación 1, confirmando que
`src/covid_analytics/pipeline.py` orquesta correctamente las tres capas (T113).

## Validación 3 — Consistencia aritmética (SC-002 / FR-007)

```bash
uv run python - <<'PY'
import pandas as pd

silver = pd.read_parquet("data/silver/casos_unificados.parquet")
demografia = pd.read_parquet("data/gold/metricas_demografia.parquet")
series = pd.read_parquet("data/gold/series_temporales.parquet")

assert demografia["total_casos"].sum() == len(silver), "Discrepancia en metricas_demografia"
assert series[["casos_notificados"]].sum().sum() <= len(silver), "Discrepancia en series_temporales"
print("OK: consistencia marginal verificada")
PY
```

**Resultado esperado**: `OK: consistencia marginal verificada` sin `AssertionError`.

## Validación 4 — Cero PII en artefactos Gold (SC-001)

```bash
uv run python - <<'PY'
import pandas as pd

for tabla in ["metricas_demografia", "series_temporales", "distribucion_geografica", "kpis_generales"]:
    df = pd.read_parquet(f"data/gold/{tabla}.parquet")
    columnas_prohibidas = {"nombre", "telefono", "domicilio", "curp", "paciente_id"}
    assert not (set(df.columns) & columnas_prohibidas), f"PII detectado en {tabla}"
print("OK: cero columnas PII en capa Gold")
PY
```

**Resultado esperado**: `OK: cero columnas PII en capa Gold`.

## Validación 5 — El Guantelete

```bash
uv run mypy --strict src
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest --cov=src --cov-fail-under=90
```

**Resultado esperado**: los cuatro comandos terminan en verde (código de salida `0`), con
cobertura de pruebas >= 90% incluyendo los nuevos módulos `analytics/*`.

## Referencias

- Esquemas de tablas: [`data-model.md`](./data-model.md)
- Contratos de datos por tabla: [`contracts/`](./contracts/)
- Tareas de implementación: [`tasks.md`](./tasks.md)
