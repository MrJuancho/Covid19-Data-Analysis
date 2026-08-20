# Implementation Plan: Dashboard Epidemiológico Interactivo (Streamlit)

**Branch**: `003-dashboard-epidemiologico` | **Date**: 2026-08-19 | **Spec**: [specs/003-dashboard-epidemiologico/spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-dashboard-epidemiologico/spec.md`

## Summary

Construir un tablero Streamlit (`src/covid_analytics/ui/`) que consuma exclusivamente los Parquet de la capa Gold (`data/gold/*.parquet`) y el reporte de calidad de Silver (`data/silver/data_quality_summary.json`), con filtros reactivos (fechas, sexo, grupo etario, derechohabiencia), 4 tarjetas KPI y 5 pestañas (curva epidemiológica, demografía/pirámide, geoespacial, riesgo clínico, calidad). Requiere primero extender la capa Gold existente (`src/covid_analytics/analytics/`) con dos piezas que el tablero necesita y que 002-covid-gold no expone: una columna `grupo_edad_ui` de cortes exactos (FR-005a) y una nueva tabla `metricas_derechohabiencia.parquet` (FR-006a).

## Technical Context

**Language/Version**: Python 3.12 (consistente con 001/002-covid-gold)

**Primary Dependencies**: `streamlit` (UI + `streamlit.testing.v1.AppTest`), `plotly` (todos los gráficos, incluido el mapa vía `choropleth_map`/`choropleth_mapbox`), `pyshp` (lectura de `mapa_mexico/*.shp` → GeoJSON, sin requerir GDAL/geopandas); reutiliza `pandas`, `pyarrow`, `pydantic` ya presentes en el proyecto para la extensión de Gold.

**Storage**: Lectura únicamente — `data/gold/*.parquet` (5 archivos, uno nuevo), `data/silver/data_quality_summary.json`, `mapa_mexico/Division_Municipal_Mexico_2010.shp` (estático, ya presente en el repo). Cero escritura desde la UI.

**Testing**: `pytest` + `pytest-cov` (`--cov=src --cov-fail-under=90`); lógica de filtrado/agregación en `ui/filtros.py` y `ui/data_loader.py` se prueba con `pytest` puro (sin runtime de Streamlit); `tests/unit/test_ui_app.py` usa `streamlit.testing.v1.AppTest` para smoke tests de la app completa. Extiende `tests/fixtures/silver_sintetico.py` (derechohabiencia variada) y añade fixtures de Parquet Gold sintéticos para la UI.

**Target Platform**: Navegador local vía `streamlit run` (servidor de desarrollo local, CLI); mismo entorno Windows/local del resto del proyecto.

**Project Type**: Single project — extensión de un paquete Python existente (`covid_analytics`) con un nuevo subpaquete de presentación (`ui/`).

**Performance Goals**: SC-002 (spec) — cambio de filtro re-renderiza en <2s; SC-003 (spec) — carga inicial completa (KPIs + 5 pestañas) en <5s, sobre volúmenes típicos del hospital (miles de filas Silver, cientos/miles de filas Gold agregadas, igual orden de magnitud que 002-covid-gold).

**Constraints**: Cero PII en pantalla/logs (Principio I, FR-002, SC-004); cero transformaciones pesadas en tiempo de renderizado — toda agregación de dimensiones nuevas (`grupo_edad_ui`, `derechohabiencia`) ocurre en Gold, no en la UI (Principio II); tipado estricto `mypy --strict src` (Principio III); degradación por pestaña ante artefactos Gold individuales ausentes (FR-013).

**Scale/Scope**: Un solo usuario/sesión local, sin autenticación (Assumptions de spec.md); 5 pestañas, 4 tarjetas KPI, 4 filtros de sidebar; 2 extensiones aditivas a la capa Gold existente.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Gate | Estado |
|---|---|---|
| I. Privacidad y Anonimización | Cero PII en la UI; solo Gold + reporte de calidad Silver (whitelist explícita, FR-002) | PASS — ninguna fuente leída contiene identificadores individuales |
| II. Arquitectura Medallion | Extensión de Gold en `src/covid_analytics/analytics/` (FR-005a, FR-006a); presentación aislada en `src/covid_analytics/ui/`, estrictamente downstream, sin lógica de agregación nueva | PASS — separación estricta de módulos por capa |
| III. El Guantelete | `mypy --strict`, `ruff`, `pytest >= 90%` con fixtures sintéticos + `AppTest` | PASS — se agregarán fixtures y suites TDD para cada módulo nuevo |
| IV. SDD Estricto | `spec.md` (clarificado) → `plan.md` → `tasks.md` antes de implementar; TDD estricto | PASS — 3 ambigüedades resueltas en `/speckit-clarify`, contratos completos en este plan |

## Project Structure

### Documentation (this feature)

```text
specs/003-dashboard-epidemiologico/
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
    ├── models.py                       # Extensión: MetricasDemografiaGold.grupo_edad_ui,
    │                                    # nuevo modelo MetricasDerechohabienciaGold
    ├── analytics/                      # Capa Gold (Principio II) — extensión, no nueva capa
    │   ├── demografia.py               # + calcular grupo_edad_ui (cortes exactos 18/40/60)
    │   ├── derechohabiencia.py         # NUEVO: cubo (derechohabiencia × resultado × estatus)
    │   ├── engine.py                   # Orquesta la nueva tabla + columna, persistencia
    │   └── _shared.py                  # Reutilizado: tasa_segura, GoldIntegrityError
    ├── pipeline.py                     # Sin cambios de contrato (ya invoca generar_capa_gold)
    └── ui/                             # NUEVO paquete: capa de presentación (Principio II)
        ├── __init__.py
        ├── data_loader.py              # @st.cache_data / @st.cache_resource: carga resiliente
        │                                # de los 5 Parquet Gold + JSON de calidad + GeoJSON
        ├── filtros.py                  # FiltroTablero (dataclass) + funciones puras de
        │                                # filtrado/recorte sobre DataFrames Gold ya agregados
        └── app.py                      # Entrypoint Streamlit: sidebar, KPIs, 5 pestañas
                                         # (orquestación delgada sobre data_loader + filtros)

tests/
├── fixtures/
│   └── silver_sintetico.py             # Extendido: derechohabiencia variada, edades de borde
│                                        # (36-40, 56-60) para validar grupo_edad_ui
└── unit/
    ├── test_analytics_demografia.py    # + tests de grupo_edad_ui
    ├── test_analytics_derechohabiencia.py  # NUEVO
    ├── test_ui_data_loader.py          # NUEVO: carga resiliente, cero PII, cache
    ├── test_ui_filtros.py              # NUEVO: FiltroTablero + funciones puras (sin Streamlit)
    └── test_ui_app.py                  # NUEVO: smoke tests con streamlit.testing.v1.AppTest
```

**Structure Decision**: Proyecto único existente, sin nueva capa de build. La extensión de Gold vive junto a los módulos ya establecidos en `src/covid_analytics/analytics/` (mismo patrón de 002-covid-gold: un módulo por dimensión + `engine.py` como orquestador). La UI es un subpaquete nuevo y aislado (`src/covid_analytics/ui/`) que solo importa desde `covid_analytics.models` (tipos) y lee Parquet/JSON de disco — nunca importa `cleaning/` ni `ingestion/`, preservando el Principio II. La lógica de filtrado (`filtros.py`) se mantiene libre de `streamlit` como dependencia para maximizar cobertura de tests puros sin necesitar `AppTest` en cada caso.
