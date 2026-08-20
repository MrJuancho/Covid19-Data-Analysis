# Implementation Plan: Pipeline ETL de COVID-19 (Bronze a Silver)

**Branch**: `001-covid-etl` | **Date**: 2026-08-19 | **Spec**: [specs/001-covid-etl/spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-covid-etl/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Reemplazar la ingesta posicional (`iloc`) y frágil de `data_analysis.py` por un pipeline
ETL de dos capas (Bronze → Silver) que: (1) lee las 3 hojas del Excel origen localizando
encabezados por nombre y acotando memoria, (2) seudonimiza PII con SHA-256 inmediatamente
en Bronze, (3) normaliza demografía/fechas/categorías con un catálogo canónico en Silver,
(4) cruza heurísticamente Seguimiento↔Nominal por `paciente_id + edad + sexo` con ventana
de 7 días, y (5) persiste `casos_unificados.parquet` + `data_quality_summary.json`. El
enfoque técnico (research.md) usa `uv` + `pandas`/`openpyxl` para ingesta acotada,
`pydantic` como contrato de tipos en las fronteras de módulo (para satisfacer
`mypy --strict`), y `pyarrow` para la escritura Parquet con compresión Snappy.

## Technical Context

**Language/Version**: Python 3.12 (versión instalada en el entorno de desarrollo; sin
requisito de compatibilidad hacia abajo indicado en `spec.md`)

**Primary Dependencies**: `pandas`, `openpyxl` (lectura Excel en modo acotado/read-only),
`pydantic` (contratos `CasoBronze`/`CasoUnificadoSilver`/`ResumenCalidad`), `pyarrow`
(escritura Parquet, compresión Snappy)

**Storage**: Archivos locales — `data/silver/casos_unificados.parquet` (Parquet) y
`data/silver/data_quality_summary.json` (JSON). N/A base de datos.

**Testing**: `pytest` + `pytest-cov` (gate `--cov-fail-under=90`, Principio III de la
Constitución); fixtures exclusivamente sintéticas, nunca el `.xlsx` real con PII (User
Story 1, Independent Test)

**Target Platform**: Ejecución local (CLI), mismo entorno Windows/Python usado hoy para
`data_analysis.py`; sin requisito de servidor o despliegue en esta feature

**Project Type**: Pipeline de datos / CLI de un solo proyecto (`src/` + `tests/`, Option 1
de la plantilla — no aplica la variante web/mobile)

**Performance Goals**: No hay throughput objetivo explícito (dataset es ~6k filas por
hoja); el objetivo relevante es de memoria, no de velocidad (ver Constraints)

**Constraints**: Consumo pico de RAM `< 500 MB` durante la ingesta (SC-002); cero PII en
texto plano fuera de la capa Bronze (Principio I, no negociable)

**Scale/Scope**: 3 hojas de Excel, ~6,000 filas cada una en Seguimiento/Nominal, 1 corrida
por invocación de CLI (no es un servicio de larga duración ni multi-usuario)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Gate | Estado (pre-Fase 0) | Estado (post-Fase 1) |
|---|---|---|---|
| I. Privacidad y Anonimización (PII First) | Ninguna columna PII en texto plano fuera de Bronze; hash SHA-256 en Bronze | PASS — arquitectura de capas + `data-model.md` garantizan que `CasoBronze` es la única estructura que ve PII en memoria y nunca se persiste | PASS — `contracts/casos_unificados_silver.md` declara la ausencia estructural de PII como parte del contrato |
| II. Arquitectura de Datos por Capas (Medallion) | Ingesta en `src/covid_analytics/ingestion/`, limpieza/cruce en `src/covid_analytics/cleaning/` | PASS — ver Project Structure abajo | PASS — sin cambios tras el diseño de Fase 1 |
| III. Calidad de Código y Gates Obligatorios ("El Guantelete") | `mypy --strict`, `ruff check`/`format`, `pytest --cov-fail-under=90`, fixtures sintéticas | PASS con acción previa requerida — no existe `pyproject.toml`/`uv.lock` todavía; `research.md#1` fija que la primera tarea de implementación debe hacer `uv init` antes de escribir código de negocio | PASS — `research.md#5` fija el uso de contratos Pydantic en las fronteras de módulo específicamente para que `mypy --strict` sea alcanzable sobre código pandas |
| IV. Desarrollo Dirigido por Especificaciones (SDD Estricto) | `spec.md` → `plan.md` → `tasks.md` antes de implementar; TDD estricto; auditoría dual Gemini | PASS — este plan se genera después de `spec.md` y de la Constitución ratificada; `tasks.md` es el siguiente paso obligatorio antes de cualquier código | PASS — sin cambios; la auditoría dual de Gemini ocurre en revisión de PR, fuera del alcance de este comando |

Sin violaciones que requieran `Complexity Tracking`.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
└── covid_analytics/
    ├── __init__.py
    ├── pipeline.py            # CLI entrypoint (contracts/pipeline_cli.md)
    ├── models.py               # Pydantic: CasoBronze, CasoUnificadoSilver, ResumenCalidad
    ├── ingestion/               # Capa Bronze (Principio II)
    │   ├── __init__.py
    │   ├── excel_reader.py     # lectura acotada + detección de encabezado por nombre
    │   └── pii.py               # normalización de nombre + hash SHA-256 (Principio I)
    └── cleaning/                 # Capa Silver (Principio II)
        ├── __init__.py
        ├── fechas.py             # parse_fecha_polimorfica (research.md #3)
        ├── catalogos.py          # catálogo canónico municipio/estatus_paciente/resultado_prueba
        ├── demografia.py         # unificación edad/sexo + corrector de columnas intercambiadas
        └── merge.py               # cruce heurístico Seguimiento↔Nominal (User Story 3)

tests/
├── unit/
│   ├── test_pii.py
│   ├── test_fechas.py
│   ├── test_demografia.py
│   └── test_catalogos.py
├── integration/
│   ├── test_pipeline_end_to_end.py
│   └── test_merge_heuristico.py
└── fixtures/
    └── excel_sintetico.py       # generador de .xlsx sintético (nunca el real con PII)

data/
└── silver/                       # salida del pipeline (gitignored salvo .gitkeep)
```

**Structure Decision**: Opción 1 (proyecto único) — no aplica la variante web/mobile
porque no hay frontend/backend separados ni app móvil en el alcance de `spec.md`. Los
paths coinciden exactamente con los que la Constitución fija en el Principio II
(`src/covid_analytics/ingestion/`, `src/covid_analytics/cleaning/`) y con las rutas ya
referenciadas explícitamente en `spec.md` (FR-001, FR-008). `analytics/` (capa Gold) no se
crea todavía — está fuera del alcance de esta feature (spec.md cubre Bronze→Silver) y se
añadirá en una feature futura sin romper este contrato.

## Complexity Tracking

*Sin violaciones — la tabla de Constitution Check arriba no registra ningún PASS
condicionado a una excepción; no aplica esta sección.*
