# Quickstart: Validar el Pipeline ETL de COVID-19 (Bronze a Silver)

Guía de validación de extremo a extremo. No incluye código de implementación — solo
comandos ejecutables y resultados esperados. Referencias de esquema en `data-model.md` y
`contracts/`.

## Prerrequisitos

- Python 3.12 con [`uv`](https://docs.astral.sh/uv/) instalado.
- Proyecto `uv` inicializado en la raíz (`pyproject.toml` + `uv.lock`; ver
  `research.md#1`) con dependencias: `pandas`, `pydantic`, `pyarrow`, `openpyxl`,
  `pytest`, `pytest-cov`, `mypy`, `ruff`.
- El archivo fuente
  `RED-NEGATIVA-COVID-02_VIGILANCIA-HOSPITALARIA 11.01.21.xlsx` presente en la raíz del
  repo (ya está en el working tree; contiene PII real — no debe salir del entorno local).
- Variable de entorno `COVID_PII_SALT` configurada (opcional en local; ver
  `contracts/pipeline_cli.md`).

## 1. Instalar dependencias

```bash
uv sync
```

**Resultado esperado**: `uv.lock` resuelto sin errores.

## 2. Ejecutar "El Guantelete" (gates de calidad, Principio III)

```bash
uv run mypy --strict src
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest --cov=src --cov-fail-under=90
```

**Resultado esperado**: los 4 comandos terminan con código de salida `0`. `pytest` reporta
cobertura `>= 90%` usando exclusivamente fixtures sintéticos (ningún test debe abrir el
`.xlsx` real con PII — ver User Story 1, "Independent Test").

## 3. Ejecutar el pipeline sobre el Excel real (validación manual, no en CI)

```bash
uv run python -m covid_analytics.pipeline \
  --excel-path "RED-NEGATIVA-COVID-02_VIGILANCIA-HOSPITALARIA 11.01.21.xlsx" \
  --output-dir data/silver
```

**Resultado esperado**:
- Código de salida `0`.
- Uso pico de RAM del proceso `< 500 MB` (SC-002) — verificar con el monitor de recursos
  del sistema operativo durante la corrida.
- Se crean `data/silver/casos_unificados.parquet` y `data/silver/data_quality_summary.json`
  (o la ruta indicada en `--output-dir`).

## 4. Validar el contrato de salida Silver

```bash
uv run python -c "
import pandas as pd
df = pd.read_parquet('data/silver/casos_unificados.parquet')
assert set(df.columns) >= {
    'paciente_id', 'edad', 'sexo', 'municipio_residencia', 'derechohabiencia',
    'fecha_notificacion', 'fecha_toma_muestra', 'fecha_resultado', 'resultado_prueba',
    'estatus_paciente', 'es_registro_unificado', 'dias_entre_notificacion_e_ingreso',
}
assert df['paciente_id'].str.len().eq(64).all()
pii_cols = {'CASO', 'NOMBRE DEL PACIENTE', 'CALLE', 'TELEFONO'}
assert not pii_cols & set(df.columns)
print('OK:', len(df), 'filas')
"
```

**Resultado esperado**: imprime `OK: <N> filas` sin `AssertionError` — confirma el
contrato de `contracts/casos_unificados_silver.md` y la ausencia estructural de PII
(Principio I).

## 5. Validar el reporte de calidad

```bash
uv run python -c "
import json
r = json.load(open('data/silver/data_quality_summary.json', encoding='utf-8'))
assert all(v is not None for v in r.values())
assert r['filas_leidas_bronze_seguimiento'] > 0
assert r['filas_leidas_bronze_nominal'] > 0
print('OK:', r)
"
```

**Resultado esperado**: imprime el resumen sin `AssertionError` — confirma el contrato de
`contracts/data_quality_summary.md` (SC-003).

## 6. Validar el escenario de cruce heurístico (User Story 3)

Ejecutar la suite de tests de integración específica del merge (definida en
`tasks.md` cuando exista):

```bash
uv run pytest tests/integration/test_merge_heuristico.py -v
```

**Resultado esperado**: los casos "mismo `paciente_id`, ventana ≤7 días → se fusionan" y
"ventana >7 días → quedan huérfanos" (Acceptance Scenarios 1 y 2 de User Story 3) pasan en
verde.
