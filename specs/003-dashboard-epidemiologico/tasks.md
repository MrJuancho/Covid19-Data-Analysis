# Tasks: Dashboard Epidemiológico Interactivo (Streamlit)

**Input**: Design documents from `/specs/003-dashboard-epidemiologico/`

**Prerequisites**: `spec.md` (clarificado), `plan.md`, `research.md`, `data-model.md`, `contracts/` (todos presentes).

**Tests & TDD**: TDD estricto (Principio IV de la Constitución). Claude Code DEBE escribir primero las pruebas unitarias que fallen antes de implementar la lógica de negocio correspondiente. `ui/filtros.py` y `ui/data_loader.py` se prueban con `pytest` puro (sin runtime de Streamlit); `ui/app.py` se prueba con `streamlit.testing.v1.AppTest` (FR-014).

---

## Phase 1: Setup

- [X] T001 Añadir `streamlit`, `plotly`, `pyshp` a las dependencias de `pyproject.toml` y ejecutar `uv sync`
- [X] T002 [P] Crear el esqueleto del paquete `src/covid_analytics/ui/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRÍTICO**: Ninguna historia de usuario puede comenzar hasta que esta fase esté completa.

- [X] T003 [P] Crear `tests/fixtures/gold_sintetico.py`: builders de DataFrames/Parquet sintéticos para los 5 archivos de `data/gold/`, `data_quality_summary.json` y un shapefile mínimo de prueba, reutilizados por las 5 historias de UI
- [X] T004 [P] Definir `FiltroTablero` y `VistaKPI` (dataclasses puras, sin `streamlit`) en `src/covid_analytics/ui/filtros.py` (`contracts/ui_filtros_interface.md`)
- [X] T005 [P] Escribir tests de los 7 loaders (carga resiliente ante archivo ausente, cero PII, invalidación de caché por mtime) en `tests/unit/test_ui_data_loader.py` ⚠️ (Escribir primero, verificar que fallan)
- [X] T006 Implementar `cargar_metricas_demografia`, `cargar_series_temporales`, `cargar_distribucion_geografica`, `cargar_kpis_generales`, `cargar_metricas_derechohabiencia`, `cargar_reporte_calidad` y `cargar_geojson_municipios` en `src/covid_analytics/ui/data_loader.py` con `@st.cache_data`/`@st.cache_resource` (`contracts/ui_data_loader_interface.md`)
- [X] T007 Crear el esqueleto de `src/covid_analytics/ui/app.py`: `st.set_page_config`, estado global "ningún archivo Gold existe", sidebar con los 4 filtros (`filtro_fechas`, `filtro_sexo`, `filtro_grupo_edad`, `filtro_derechohabiencia`, keys de `contracts/app_layout_contract.md`) y `st.tabs` con las 5 pestañas como placeholders

**Checkpoint**: Infraestructura de carga, filtrado y layout lista — las historias de usuario pueden implementarse en paralelo.

---

## Phase 3: User Story 1 - Curva Epidemiológica y KPIs Globales (Priority: P1) 🎯 MVP

**Goal**: Curva de casos diarios con media móvil de 7 días y las 4 tarjetas KPI, reactivas al filtro de fechas.

**Independent Test**: Con `series_temporales.parquet`/`kpis_generales.parquet` sintéticos, mover el slider de fechas a un subrango y verificar que la curva, la media móvil y las 4 tarjetas KPI se recalculan sin recarga completa.

### Tests

- [X] T008 [P] [US1] Escribir tests de `aplicar_filtro_series` y `calcular_vista_kpi` en `tests/unit/test_ui_filtros.py` ⚠️ (Escribir primero, verificar que fallan)
- [X] T009 [P] [US1] Escribir smoke tests con `AppTest` de las tarjetas KPI y la Pestaña 1 (incl. cambio de rango de fechas) en `tests/unit/test_ui_app.py` ⚠️ (Escribir primero, verificar que fallan)

### Implementación

- [X] T010 [US1] Implementar `aplicar_filtro_series` y `calcular_vista_kpi` en `src/covid_analytics/ui/filtros.py`
- [X] T011 [US1] Renderizar las 4 tarjetas KPI (`st.metric`) y la Pestaña 1 (curva + media móvil 7d con Plotly Express) en `src/covid_analytics/ui/app.py`, reactivas al filtro de fechas

**Checkpoint**: User Story 1 (MVP) funcional y demostrable de forma independiente.

---

## Phase 4: User Story 2 - Demografía y Pirámide Poblacional (Priority: P2)

**Goal**: Pirámide poblacional (edad × sexo) y tasa de positividad por grupo etario, reactivas a los filtros de sexo y grupo etario, usando la nueva columna exacta `grupo_edad_ui` (FR-005a).

**Independent Test**: Con `metricas_demografia.parquet` sintético (incluyendo edades de borde 36-40/56-60), aplicar el multiselector de sexo a un solo valor y verificar que la pirámide y las tarjetas KPI excluyen a los demás sexos con coincidencia exacta.

### Tests

- [X] T012 [P] [US2] Extender `tests/fixtures/silver_sintetico.py` con edades de borde (36-40, 56-60) que validan la desalineación de límites resuelta en `/speckit-clarify`
- [X] T013 [P] [US2] Escribir tests de `asignar_grupo_edad_ui` y de la extensión de `calcular_metricas_demografia` (grano `grupo_edad × grupo_edad_ui`) en `tests/unit/test_analytics_demografia.py` ⚠️ (Escribir primero, verificar que fallan)
- [X] T014 [P] [US2] Escribir tests de `aplicar_filtro_demografia` (coincidencia exacta de sexo, ver Clarifications) en `tests/unit/test_ui_filtros.py` ⚠️ (Escribir primero, verificar que fallan)
- [X] T015 [P] [US2] Escribir smoke tests con `AppTest` de la Pestaña 2 (pirámide completa sin filtro, filtro `FEMENINO` exacto) en `tests/unit/test_ui_app.py` ⚠️ (Escribir primero, verificar que fallan)

### Implementación

- [X] T016 [US2] Implementar `asignar_grupo_edad_ui` (cortes exactos 18/40/60, `contracts/metricas_demografia_gold_extension.md`) y extender `calcular_metricas_demografia` en `src/covid_analytics/analytics/demografia.py`; añadir campo `grupo_edad_ui` a `MetricasDemografiaGold` en `src/covid_analytics/models.py`
- [X] T017 [US2] Extender `verificar_consistencia_marginal` en `src/covid_analytics/analytics/engine.py` para validar también la dimensión `grupo_edad_ui`
- [X] T018 [US2] Implementar `aplicar_filtro_demografia` en `src/covid_analytics/ui/filtros.py`
- [X] T019 [US2] Renderizar la Pestaña 2 (pirámide edad×sexo y barras de tasa de positividad por grupo etario) en `src/covid_analytics/ui/app.py`, reactiva a los filtros de sexo y grupo etario

**Checkpoint**: User Stories 1 y 2 funcionan de forma independiente.

---

## Phase 5: User Story 3 - Distribución Geoespacial (Priority: P2)

**Goal**: Mapa de concentración de casos por municipio, acotado a la zona de influencia hospitalaria.

**Independent Test**: Con `distribucion_geografica.parquet` sintético (varios municipios de la zona de influencia) y el GeoJSON de prueba, renderizar el mapa y verificar que cada municipio se colorea sin errores de unión geográfica.

### Tests

- [X] T020 [P] [US3] Escribir smoke tests con `AppTest` de la Pestaña 3 (mapa renderiza, municipio sin geometría se omite sin romper la vista) en `tests/unit/test_ui_app.py` ⚠️ (Escribir primero, verificar que fallan)

### Implementación

- [X] T021 [US3] Renderizar la Pestaña 3 (`plotly.express.choropleth_map`/`choropleth_mapbox` acotado a la zona de influencia, uniendo `distribucion_geografica.parquet` con el GeoJSON cacheado por `municipio_residencia`) en `src/covid_analytics/ui/app.py`

**Checkpoint**: User Stories 1, 2 y 3 funcionan de forma independiente.

---

## Phase 6: User Story 4 - Riesgo Clínico por Derechohabiencia (Priority: P3)

**Goal**: Barras apiladas de derechohabiencia vs. tasa de hospitalización/resultado, reactivas al nuevo filtro de derechohabiencia, usando la nueva tabla `metricas_derechohabiencia.parquet` (FR-006a).

**Independent Test**: Con `metricas_derechohabiencia.parquet` sintético, filtrar por una derechohabiencia específica y verificar que el gráfico muestra únicamente esa afiliación; con el archivo ausente, verificar degradación por pestaña sin afectar al resto del tablero.

### Tests

- [X] T022 [P] [US4] Extender `tests/fixtures/silver_sintetico.py` con derechohabiencia variada (incl. valores no reconocidos, ej. `SEDENA`, para validar la categoría `OTRA`)
- [X] T023 [P] [US4] Escribir tests de `estandarizar_derechohabiencia` y `calcular_metricas_derechohabiencia` en `tests/unit/test_analytics_derechohabiencia.py` ⚠️ (Escribir primero, verificar que fallan)
- [X] T024 [P] [US4] Escribir tests de `aplicar_filtro_derechohabiencia` en `tests/unit/test_ui_filtros.py` ⚠️ (Escribir primero, verificar que fallan)
- [X] T025 [P] [US4] Escribir smoke tests con `AppTest` de la Pestaña 4 y de la degradación por pestaña cuando falta `metricas_derechohabiencia.parquet` en `tests/unit/test_ui_app.py` ⚠️ (Escribir primero, verificar que fallan)

### Implementación

- [X] T026 [US4] Implementar `src/covid_analytics/analytics/derechohabiencia.py` (`estandarizar_derechohabiencia`, `calcular_metricas_derechohabiencia`, `contracts/metricas_derechohabiencia_gold.md`); añadir modelo `MetricasDerechohabienciaGold` en `src/covid_analytics/models.py`
- [X] T027 [US4] Integrar `metricas_derechohabiencia.parquet` en `generar_capa_gold` y extender `verificar_consistencia_marginal` (positivos por derechohabiencia) en `src/covid_analytics/analytics/engine.py`
- [X] T028 [US4] Implementar `aplicar_filtro_derechohabiencia` en `src/covid_analytics/ui/filtros.py`
- [X] T029 [US4] Renderizar la Pestaña 4 (barras apiladas derechohabiencia vs. hospitalización/resultado) en `src/covid_analytics/ui/app.py`, reactiva al filtro de derechohabiencia, con estado "no disponible" si falta el archivo (FR-013)

**Checkpoint**: User Stories 1-4 funcionan de forma independiente.

---

## Phase 7: User Story 5 - Calidad y Telemetría del Pipeline (Priority: P3)

**Goal**: Vista del reporte `data_quality_summary.json` completo, con manejo explícito de archivo ausente.

**Independent Test**: Con un `data_quality_summary.json` sintético, verificar que la Pestaña 5 muestra cada campo del reporte; con el archivo ausente, verificar el mensaje de "reporte no disponible".

### Tests

- [X] T030 [P] [US5] Escribir smoke tests con `AppTest` de la Pestaña 5 (reporte presente y ausente) en `tests/unit/test_ui_app.py` ⚠️ (Escribir primero, verificar que fallan)

### Implementación

- [X] T031 [US5] Renderizar la Pestaña 5 (contenido íntegro de `data_quality_summary.json`, incluyendo `fechas_anomalas_fuera_ventana`) en `src/covid_analytics/ui/app.py`, con mensaje explícito si el reporte no existe

**Checkpoint**: Las 5 historias de usuario funcionan de forma independiente.

---

## Phase 8: Polish & El Guantelete

- [X] T032 [P] Regenerar `data/gold/*.parquet` (incluyendo `metricas_derechohabiencia.parquet` y la columna `grupo_edad_ui`) ejecutando `engine.py` sobre `data/silver/casos_unificados.parquet` (`quickstart.md` Validación 1)
- [X] T033 [P] Ejecutar `quickstart.md` Validaciones 2 y 5 (consistencia de las nuevas dimensiones, cero PII en los 5 Parquet)
- [X] T034 [P] Escribir un test de rendimiento del pipeline `data_loader` + `filtros` (proxy de SC-002/SC-003) en `tests/unit/test_ui_app.py`
- [X] T035 Ejecutar "El Guantelete" completo:
  - `uv run mypy --strict src`
  - `uv run ruff check src tests`
  - `uv run ruff format --check src tests`
  - `uv run pytest --cov=src --cov-fail-under=90`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias — puede iniciar de inmediato.
- **Foundational (Phase 2)**: depende de Setup — BLOQUEA todas las historias de usuario.
- **User Stories (Phase 3-7)**: todas dependen de Foundational. Entre sí son independientes salvo
  que comparten el mismo archivo `src/covid_analytics/ui/app.py` (cada historia añade su propia
  pestaña sin tocar las demás) — ejecutarlas en el orden de prioridad P1→P2→P2→P3→P3 evita
  conflictos de merge, aunque no hay dependencia funcional entre ellas.
- **Polish (Phase 8)**: depende de que todas las historias deseadas estén completas.

### User Story Dependencies

- **US1 (P1)**: solo depende de Foundational.
- **US2 (P2)**: solo depende de Foundational (su trabajo de Gold, FR-005a, es autocontenido).
- **US3 (P2)**: solo depende de Foundational (`cargar_geojson_municipios` ya implementado en T006).
- **US4 (P3)**: solo depende de Foundational (su trabajo de Gold, FR-006a, es autocontenido).
- **US5 (P3)**: solo depende de Foundational (`cargar_reporte_calidad` ya implementado en T006).

### Dentro de cada Historia

- Tests (T0xx marcados ⚠️) DEBEN escribirse y fallar antes de la implementación correspondiente.
- Trabajo de Gold (cuando aplica: US2, US4) antes que el filtro de UI correspondiente.
- Filtro de UI (`filtros.py`) antes que el renderizado de la pestaña en `app.py`.

### Oportunidades de Paralelismo

- Todas las tareas [P] de Foundational (T003-T005) pueden ejecutarse en paralelo.
- Una vez completa Foundational, **US1, US2, US3, US4 y US5 pueden implementarse en paralelo**
  por desarrolladores distintos (cada una toca archivos de Gold/tests propios; solo convergen al
  añadir su pestaña a `app.py`, un conflicto de merge trivial, no una dependencia funcional).
- Dentro de cada historia, todas las tareas de test marcadas [P] pueden ejecutarse en paralelo
  entre sí (archivos distintos) antes de comenzar la implementación.

---

## Parallel Example: User Story 2

```bash
# Lanzar en paralelo las 4 tareas de test de US2 (archivos distintos):
Task: "Extender tests/fixtures/silver_sintetico.py con edades de borde (T012)"
Task: "Tests de asignar_grupo_edad_ui en tests/unit/test_analytics_demografia.py (T013)"
Task: "Tests de aplicar_filtro_demografia en tests/unit/test_ui_filtros.py (T014)"
Task: "Smoke tests AppTest de la Pestaña 2 en tests/unit/test_ui_app.py (T015)"
```

---

## Implementation Strategy

### MVP First (User Story 1 únicamente)

1. Completar Fase 1: Setup
2. Completar Fase 2: Foundational (CRÍTICO — bloquea todas las historias)
3. Completar Fase 3: User Story 1
4. **DETENER y VALIDAR**: probar User Story 1 de forma independiente (`quickstart.md` Validación 3, solo Pestaña 1)
5. Desplegar/demostrar si está listo

### Entrega Incremental

1. Setup + Foundational → base lista
2. + US1 → probar de forma independiente → Demo (¡MVP!)
3. + US2 → probar de forma independiente → Demo
4. + US3 → probar de forma independiente → Demo
5. + US4 → probar de forma independiente → Demo
6. + US5 → probar de forma independiente → Demo
7. Fase 8 (Polish & Guantelete) → cierre de la feature

### Estrategia de Equipo Paralelo

Con varios desarrolladores, tras completar Foundational: un desarrollador por historia (US1-US5)
en paralelo; cada una es autocontenida salvo por la convergencia trivial en `app.py` (una nueva
pestaña por historia, sin tocar las pestañas de las demás).
