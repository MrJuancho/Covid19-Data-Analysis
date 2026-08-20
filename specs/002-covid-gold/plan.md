# Implementation Plan: Capa Gold de Analítica y Agregaciones Epidemiológicas

**Branch**: `002-covid-gold` | **Date**: 2026-08-19 | **Spec**: [specs/002-covid-gold/spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-covid-gold/spec.md`

## Summary

Implementar la capa Gold (`src/covid_analytics/analytics/`) para procesar el dataset normalizado `data/silver/casos_unificados.parquet` y producir:
1. Tablas dimensionales agregadas: `metricas_demografia.parquet`, `series_temporales.parquet`, `distribucion_geografica.parquet` y `kpis_generales.parquet`.
2. Resumen ejecutivo macro: `data/gold/resumen_ejecutivo.json`.
3. Contratos y validadores de integridad estadística para asegurar 100% de consistencia con la capa Silver.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: `pandas`, `pyarrow`, `pydantic`  
**Storage**: Directorio local `data/gold/` (archivos Parquet Snappy y JSON)  
**Testing**: `pytest` + `pytest-cov` (`--cov=src --cov-fail-under=90`), pruebas sobre fixtures sintéticos generados en `tests/fixtures/silver_sintetico.py`  
**Target Platform**: CLI local  
**Constraints**: Cero PII (Principio I), Tipado estricto `mypy --strict src` (Principio III), Tiempo de ejecución < 5s (SC-003).

## Constitution Check

| Principio | Gate | Estado |
|---|---|---|
| I. Privacidad y Anonimización | Cero PII en capa Gold; solo identificadores anónimos o agregaciones de grupo | PASS — La entrada Silver carece de PII y las salidas Gold son tablas agregadas |
| II. Arquitectura Medallion | Lógica analítica aislada en `src/covid_analytics/analytics/` | PASS — Organización estricta de módulos por capa |
| III. El Guantelete | `mypy --strict`, `ruff`, `pytest >= 90%` con fixtures sintéticos | PASS — Se agregarán fixtures y suites TDD para cada módulo |
| IV. SDD Estricto | `spec.md` → `plan.md` → `tasks.md` antes de implementar; TDD estricto | PASS — Especificación y contratos completos |

## Project Structure

```text
src/
└── covid_analytics/
    ├── models.py                     # Extensión con modelos Pydantic Gold
    ├── analytics/                    # Capa Gold (Principio II)
    │   ├── __init__.py               # Orquestador: generar_capa_gold(...)
    │   ├── _shared.py                # tasa_segura(...) y GoldIntegrityError (uso común)
    │   ├── demografia.py             # Grupos etarios y cubo demográfico
    │   ├── series_tiempo.py          # Calendario continuo, medias móviles y anomalías de fechas
    │   ├── geografia.py              # Agregaciones municipales y tasas
    │   └── engine.py                 # CLI, validación de contrato de entrada, consistencia marginal y persistencia Parquet/JSON
    └── pipeline.py                   # Orquestación end-to-end (Bronze -> Silver -> Gold)

tests/
├── fixtures/
│   └── silver_sintetico.py           # Generador de DataFrames Silver sintéticos
└── unit/
    ├── test_analytics_demografia.py
    ├── test_analytics_series.py
    ├── test_analytics_geografia.py
    └── test_analytics_engine.py
```
