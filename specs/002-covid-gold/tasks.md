# Tasks: Capa Gold de Analítica y Agregaciones Epidemiológicas

**Input**: Design documents from `/specs/002-covid-gold/`

**Prerequisites**: `spec.md`, `data-model.md`, `plan.md`, `contracts/` (todos presentes).

**Tests & TDD**: TDD estricto (Principio IV de la Constitución). Claude Code DEBE escribir primero las pruebas unitarias que fallen antes de implementar la lógica de negocio correspondiente. Uso exclusivo de fixtures sintéticos en `tests/fixtures/silver_sintetico.py`.

---

## Phase 1: Setup & Data Contracts (Foundational)

- [X] T101 [P] Definir modelos Pydantic de la capa Gold (`MetricasDemografiaGold`, `SeriesTemporalesGold`, `DistribucionGeograficaGold`, `KpisGeneralesGold` con el campo `registros_unificados_cruce`) en `src/covid_analytics/models.py`
- [X] T102 [P] Crear generador de fixtures sintéticos de la capa Silver en `tests/fixtures/silver_sintetico.py` con combinaciones variadas de fechas (incluyendo fechas invertidas), edades, resultados y municipios
- [X] T103 [P] Crear esqueleto del paquete `src/covid_analytics/analytics/__init__.py`
- [X] T103b [P] Implementar `tasa_segura(numerador, denominador) -> float` y la excepción `GoldIntegrityError` en `src/covid_analytics/analytics/_shared.py` (FR-003, FR-007), con test unitario parametrizado cubriendo denominador `0`

---

## Phase 2: User Story 1 - Agregaciones Demográficas (Priority: P1) 🎯 MVP

- [X] T104 [P] [US1] Escribir tests unitarios para clasificación por grupos etarios canónicos y cálculo de tasas de positividad en `tests/unit/test_analytics_demografia.py` ⚠️ (Escribir primero, verificar que fallan)
- [X] T105 [US1] Implementar función de asignación de `grupo_edad` y agregación multidimensional `calcular_metricas_demografia(df_silver)` en `src/covid_analytics/analytics/demografia.py`

---

## Phase 3: User Story 2 - Series Temporales y Curvas Epidemiológicas (Priority: P2)

- [X] T106 [P] [US2] Escribir tests unitarios para índice temporal diario continuo, cálculo de medias móviles a 7 días, acumulación de casos y detección de fechas invertidas (`casos_fechas_invertidas`, FR-004a) en `tests/unit/test_analytics_series.py` ⚠️ (Escribir primero, verificar que fallan)
- [X] T107 [US2] Implementar motor de series temporales y lags `calcular_series_temporales(df_silver)` en `src/covid_analytics/analytics/series_tiempo.py`, incluyendo el manejo de fechas invertidas de FR-004a (lag nulo + telemetría de anomalía, sin abortar el pipeline)

---

## Phase 4: User Story 3 - Distribución Geográfica y Tasas Municipales (Priority: P2)

- [X] T108 [P] [US3] Escribir tests unitarios para agregación municipal, tasas de letalidad y hospitalización con protección contra división por cero en `tests/unit/test_analytics_geografia.py` ⚠️ (Escribir primero, verificar que fallan)
- [X] T109 [US3] Implementar agregador geográfico `calcular_distribucion_geografica(df_silver)` en `src/covid_analytics/analytics/geografia.py`

---

## Phase 5: User Story 4 - Resumen Ejecutivo, Orquestación y Persistencia (Priority: P3)

- [X] T110 [P] [US4] Escribir tests unitarios de integración para el engine analítico y verificación de consistencia marginal en `tests/unit/test_analytics_engine.py` ⚠️ (Escribir primero, verificar que fallan)
- [X] T110b [P] [US4] Escribir test unitario que valide cero columnas PII (`nombre`, `telefono`, `domicilio`, `curp`, `paciente_id`) en las cuatro tablas Gold generadas a partir de un fixture sintético (SC-001) en `tests/unit/test_analytics_engine.py` ⚠️ (Escribir primero, verificar que falla)
- [X] T111a [US4] Implementar validación del contrato de entrada Silver (FR-001) en `engine.py`: cargar `data/silver/casos_unificados.parquet` contra el esquema `CasoUnificadoSilver`, saliendo con código `1` (ver `contracts/analytics_cli.md`) si el archivo no existe o el esquema no concuerda
- [X] T111 [US4] Implementar sintetizador macro `calcular_kpis_generales(df_silver)` (incluyendo `registros_unificados_cruce`) y orquestador `generar_capa_gold(...)` en `src/covid_analytics/analytics/engine.py`
- [X] T111b [US4] Implementar `verificar_consistencia_marginal(df_silver, tablas_gold)` en `src/covid_analytics/analytics/_shared.py`/`engine.py` (FR-007, SC-002), invocada al final de `generar_capa_gold(...)` y mapeada a código de salida `2` en la CLI ante `GoldIntegrityError`
- [X] T112 [US4] Implementar persistencia en `data/gold/` (`*.parquet` Snappy + `resumen_ejecutivo.json`) y CLI en `src/covid_analytics/analytics/engine.py`
- [X] T113 [US4] Integrar capa Gold en el pipeline maestro `src/covid_analytics/pipeline.py` para permitir ejecución end-to-end (`Bronze -> Silver -> Gold`)

---

## Phase 6: Polish & El Guantelete

- [X] T114 [P] Ejecutar "El Guantelete" completo:
  - `uv run mypy --strict src`
  - `uv run ruff check src tests`
  - `uv run ruff format --check src tests`
  - `uv run pytest --cov=src --cov-fail-under=90`
- [X] T114b [P] Escribir test de rendimiento (`tests/unit/test_analytics_engine.py` o módulo dedicado) que ejecute `generar_capa_gold(...)` sobre un fixture Silver representativo y falle si el tiempo total supera 5 segundos (SC-003)
