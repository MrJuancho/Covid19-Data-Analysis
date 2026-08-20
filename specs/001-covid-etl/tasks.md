---

description: "Task list template for feature implementation"
---

# Tasks: Pipeline ETL de COVID-19 (Bronze a Silver)

**Input**: Design documents from `/specs/001-covid-etl/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md (all present)

**Tests**: Incluidos y en orden TDD estricto — no son opcionales. La Constitución
(Principio IV, "SDD Estricto") exige explícitamente: *"Claude Code DEBE escribir primero
las pruebas unitarias que fallen antes de implementar la lógica de negocio."* Todas las
pruebas usan exclusivamente el fixture sintético de `tests/fixtures/excel_sintetico.py`
(Principio III: *"Las pruebas unitarias NO DEBEN depender del Excel real con PII"*).

**Organization**: Tareas agrupadas por historia de usuario (US1–US4, spec.md) para
permitir implementación y prueba independientes de cada una.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivo distinto, sin dependencias pendientes)
- **[Story]**: Historia de usuario a la que pertenece (US1, US2, US3, US4)
- Se incluye la ruta exacta de archivo en cada descripción

## Path Conventions

Proyecto único (`src/`, `tests/` en la raíz del repo), según `plan.md#Project Structure`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización del proyecto `uv` (no existe `pyproject.toml` hoy — research.md #1)

- [X] T001 Inicializar proyecto `uv` en la raíz del repo (`uv init --package --name covid-analytics --python 3.12`), creando `pyproject.toml`
- [X] T002 Agregar dependencias de runtime `pandas`, `openpyxl`, `pydantic`, `pyarrow` (`uv add pandas openpyxl pydantic pyarrow`) en `pyproject.toml`
- [X] T003 Agregar dependencias de desarrollo `pytest`, `pytest-cov`, `mypy`, `ruff` (`uv add --dev pytest pytest-cov mypy ruff`) en `pyproject.toml`
- [X] T004 Configurar `[tool.mypy]` con `strict = true` para `src` en `pyproject.toml`
- [X] T005 Configurar `[tool.ruff]` (target-version `py312`, reglas por defecto) en `pyproject.toml`
- [X] T006 Configurar `[tool.pytest.ini_options]` con cobertura `--cov=src --cov-fail-under=90` en `pyproject.toml`
- [X] T007 [P] Crear esqueleto de paquete: `src/covid_analytics/__init__.py`, `src/covid_analytics/ingestion/__init__.py`, `src/covid_analytics/cleaning/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`, `tests/fixtures/__init__.py` (rutas de `plan.md#Project Structure`)
- [X] T008 [P] Agregar `data/silver/` a `.gitignore` (salida generada, no fuente) y crear `data/silver/.gitkeep`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Contratos de datos y fixtures compartidos que TODAS las historias necesitan

**⚠️ CRITICAL**: Ninguna historia de usuario puede comenzar hasta completar esta fase

- [X] T009 Crear modelos Pydantic `CasoBronze`, `CasoUnificadoSilver`, `ResumenCalidad` en `src/covid_analytics/models.py` (ver `data-model.md`)
- [X] T010 [P] Crear generador de Excel sintético en `tests/fixtures/excel_sintetico.py` que replica el layout de las 3 hojas reales (`RED NEGATIVA`, `SEGUIMIENTO DE CASOS COVID 19`, ` NOMINAL DE HOSPITALIZADOS`) documentado en `docs/audit_legacy.md`, con valores 100% sintéticos (incluye rango de celdas inflado simulado para poder probar el límite de memoria)

**Checkpoint**: Fundación lista — las historias de usuario pueden comenzar

---

## Phase 3: User Story 1 - Ingesta Bronze Segura y Anonimización de PII (Priority: P1) 🎯 MVP

**Goal**: Ingerir las 3 hojas del Excel de forma acotada en memoria y seudonimizar PII con
SHA-256 inmediatamente, sin que columnas de nombre/dirección/teléfono en texto plano
salgan de la capa Bronze.

**Independent Test**: Alimentar `excel_sintetico.py` con columnas de nombre reales
sintéticas y verificar que el DataFrame/lista de `CasoBronze` resultante tenga
`paciente_id` hasheado (64 hex) y que las columnas originales de PII no existan en la
salida (spec.md, User Story 1, Independent Test).

### Tests for User Story 1 ⚠️

> Escribir estas pruebas PRIMERO y verificar que fallan antes de implementar (Principio IV)

- [X] T011 [P] [US1] Test unitario de `normalizar_nombre`/`generar_hash_pii` (incluye Edge Case de folio ausente → hash con máscara determinista) en `tests/unit/test_pii.py`
- [X] T012 [P] [US1] Test unitario de detección de encabezado por texto + lectura acotada (`usecols`, terminación temprana en filas vacías) en `tests/unit/test_excel_reader.py`
- [X] T013 [P] [US1] Test de integración de ingestión Bronze completa: `paciente_id` presente y hasheado, columnas PII originales ausentes, consumo de memoria acotado con el fixture de rango inflado, en `tests/integration/test_ingestion_bronze.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implementar `normalizar_nombre(texto)` y `generar_hash_pii(texto, folio, salt)` en `src/covid_analytics/ingestion/pii.py` (fórmula FR-002; depende de T011)
- [X] T015 [P] [US1] Implementar `leer_hoja_acotada(...)` (detección de encabezado real por búsqueda de texto en vez de `skiprows` fijo, `usecols` por hoja, corte temprano en filas vacías) en `src/covid_analytics/ingestion/excel_reader.py` (depende de T012)
- [X] T016 [US1] Implementar orquestación `ingerir_bronze(excel_path) -> list[CasoBronze]` en `src/covid_analytics/ingestion/__init__.py`, uniendo `pii.py` + `excel_reader.py` y eliminando las columnas PII originales inmediatamente tras el hash (depende de T014, T015, T009, T013)
- [X] T017 [US1] Conectar lectura de `COVID_PII_SALT` desde entorno con fallback documentado + `logging.warning` si está ausente en `src/covid_analytics/ingestion/pii.py` (research.md #6; depende de T014)

**Checkpoint**: User Story 1 completamente funcional y probable de forma independiente (MVP)

---

## Phase 4: User Story 2 - Limpieza y Normalización Semántica Silver (Priority: P2)

**Goal**: Normalizar edad/sexo, parsear fechas polimórficas y estandarizar categorías
(municipio, estatus_paciente, resultado_prueba) a un catálogo canónico, corrigiendo
columnas intercambiadas conocidas.

**Independent Test**: Alimentar la lógica de limpieza con vectores sintéticos de edades
no numéricas (`"RN"`, `"3M"`), fechas seriales de Excel, fechas con texto adicional, y
campos sexo/edad intercambiados; verificar que la salida cumpla los tipos de
`CasoUnificadoSilver` (spec.md, User Story 2, Independent Test).

### Tests for User Story 2 ⚠️

- [X] T018 [P] [US2] Test unitario de `parse_fecha_polimorfica` (datetime nativo, serial de Excel, string con ruido tipo `'24/03/2020  H. ZUMPANGO'`, texto no-fecha → `NaT`) en `tests/unit/test_fechas.py`
- [X] T019 [P] [US2] Test unitario de unificación demográfica (`EDAD | F`/`EDAD | M` → `edad`/`sexo`, sentinels `-1.0`/`INDETERMINADO`, corrección de intercambio sexo↔edad) en `tests/unit/test_demografia.py`
- [X] T020 [P] [US2] Test unitario del catálogo canónico de municipio (fallback `"OTROS"`) y de los diccionarios canónicos cerrados de `estatus_paciente`/`resultado_prueba` (incluye variantes legacy `RECHAZO`/`RECHAZADA`→`NO_CONCLUYENTE` y `NO SE TOMO`/`NO SE TOMÓ`→`PENDIENTE`, fallback `NO_ESPECIFICADO`) en `tests/unit/test_catalogos.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implementar `parse_fecha_polimorfica` en `src/covid_analytics/cleaning/fechas.py` (research.md #3; depende de T018)
- [X] T022 [P] [US2] Implementar catálogo canónico y `estandarizar_municipio`/`estandarizar_estatus_paciente`/`estandarizar_resultado_prueba` en `src/covid_analytics/cleaning/catalogos.py` (FR-006 municipio, FR-009 estatus_paciente/resultado_prueba; depende de T020)
- [X] T023 [US2] Implementar corrector de columnas intercambiadas Resultado↔Fecha de Resultado en `src/covid_analytics/cleaning/fechas.py` (spec.md, User Story 2, Acceptance Scenario 3; depende de T021, mismo archivo)
- [X] T024 [P] [US2] Implementar unificación demográfica + corrector de intercambio sexo↔edad en `src/covid_analytics/cleaning/demografia.py` (FR-004; depende de T019, T009)
- [X] T025 [US2] Implementar orquestación parcial `limpiar_silver(casos_bronze) -> list[CasoUnificadoSilver]` (sin cruce todavía) en `src/covid_analytics/cleaning/__init__.py`, uniendo `fechas.py` + `catalogos.py` + `demografia.py` (depende de T021, T022, T023, T024, T016)

**Checkpoint**: User Stories 1 y 2 funcionan de forma independiente

---

## Phase 5: User Story 3 - Cruce Heurístico de Seguimiento y Hospitalizados (Priority: P2)

**Goal**: Vincular registros de Seguimiento y Nominal sin folio compartido, usando la
llave sintética `paciente_id + edad + sexo` con ventana temporal máxima de 7 días.

**Independent Test**: Generar un paciente sintético con registro ambulatorio el
`2020-03-18` y registro de ingreso hospitalario el `2020-03-22`; verificar que se
unifiquen en una sola fila con estatus `HOSPITALIZADO` (spec.md, User Story 3,
Independent Test).

### Tests for User Story 3 ⚠️

- [X] T026 [P] [US3] Tests unitarios del cruce heurístico: ventana ≤7 días fusiona; ventana >7 días deja huérfanos independientes; colisión de homónimos se resuelve por menor `|Δt|` en días, en `tests/unit/test_merge.py`
- [X] T027 [P] [US3] Test de integración del cruce heurístico de extremo a extremo con el fixture sintético en `tests/integration/test_merge_heuristico.py` (ruta referenciada en `quickstart.md` paso 6)

### Implementation for User Story 3

- [X] T028 [US3] Implementar `cruzar_seguimiento_nominal(...)` (llave `paciente_id+edad+sexo`, ventana ≤7 días, resolución de colisiones por `|Δt|` mínimo, contadores de cruces/huérfanos/colisiones) en `src/covid_analytics/cleaning/merge.py` (FR-007; depende de T026, T027, T009)
- [X] T029 [US3] Integrar el cruce en `limpiar_silver` (cuenta cruces exitosos, huérfanos y colisiones para `ResumenCalidad`) en `src/covid_analytics/cleaning/__init__.py` (depende de T025, T028)

**Checkpoint**: User Stories 1, 2 y 3 funcionan de forma independiente

---

## Phase 6: User Story 4 - Persistencia de Capa Silver y Telemetría de Calidad (Priority: P3)

**Goal**: Persistir el dataset unificado en Parquet (Snappy) y un resumen de calidad en
JSON, expuestos vía un CLI (`contracts/pipeline_cli.md`).

**Independent Test**: Verificar que al concluir la ejecución completa del pipeline sobre
el fixture sintético, el Parquet se escribe correctamente y el JSON de métricas no tiene
campos nulos (spec.md, User Story 4, Independent Test).

### Tests for User Story 4 ⚠️

- [X] T030 [P] [US4] Test unitario de construcción/validación de `ResumenCalidad` (todas las métricas `>= 0`, cálculo de `porcentaje_huerfanos`) en `tests/unit/test_resumen_calidad.py`
- [X] T031 [P] [US4] Test de integración del pipeline de extremo a extremo: Parquet + JSON escritos, esquema conforme a `contracts/casos_unificados_silver.md` y `contracts/data_quality_summary.md`, cero columnas PII, en `tests/integration/test_pipeline_end_to_end.py`

### Implementation for User Story 4

- [X] T032 [US4] Implementar escritura de `casos_unificados.parquet` (engine `pyarrow`, `compression="snappy"`) en `src/covid_analytics/pipeline.py` (depende de T029)
- [X] T033 [US4] Implementar construcción y escritura de `data_quality_summary.json` a partir de `ResumenCalidad` en `src/covid_analytics/pipeline.py` (depende de T030, T029, mismo archivo que T032)
- [X] T034 [US4] Implementar CLI `main()` con `argparse` (`--excel-path`, `--output-dir`), logging estructurado sin PII, orquestando `ingerir_bronze` → `limpiar_silver` → escritura, per `contracts/pipeline_cli.md` (depende de T016, T025, T029, T032, T033, T031)
- [X] T035 [US4] Agregar guardia `if __name__ == "__main__":` y soporte `python -m covid_analytics.pipeline` en `src/covid_analytics/pipeline.py` (depende de T034)

**Checkpoint**: Las 4 historias de usuario funcionan de forma independiente; el pipeline completo corre de extremo a extremo

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validación final transversal a todas las historias

- [X] T036 [P] Ejecutar "El Guantelete" completo (`uv run mypy --strict src`, `uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run pytest --cov=src --cov-fail-under=90`) y corregir cualquier violación
- [X] T037 [P] Ejecutar manualmente los pasos 3–6 de `quickstart.md` contra el Excel real (`RED-NEGATIVA-COVID-02_VIGILANCIA-HOSPITALARIA 11.01.21.xlsx`) y registrar los resultados, verificando el límite de memoria de SC-002
- [X] T038 [P] Actualizar `README.md` con instrucciones de uso del pipeline referenciando `contracts/pipeline_cli.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias — puede empezar de inmediato
- **Foundational (Phase 2)**: depende de Setup — BLOQUEA todas las historias
- **User Stories (Phase 3–6)**: todas dependen de Foundational
  - US1 (P1) no depende de otras historias
  - US2 (P2) no depende de US1 para sus propias pruebas/lógica, pero `limpiar_silver`
    (T025) consume la salida de `ingerir_bronze` (T016) para el flujo completo
  - US3 (P2) depende de la salida de US2 (`limpiar_silver` parcial, T025) para integrarse,
    aunque su lógica de merge (T028) es unitariamente independiente
  - US4 (P3) depende de US1+US2+US3 para la orquestación completa del CLI (T034)
- **Polish (Phase 7)**: depende de que todas las historias deseadas estén completas

### Within Each User Story

- Los tests se escriben y DEBEN fallar antes de implementar (Principio IV)
- Modelos (Foundational) antes que servicios de cada historia
- Módulos de lógica pura (`pii.py`, `fechas.py`, `catalogos.py`, `demografia.py`,
  `merge.py`) antes que las funciones de orquestación que los integran
  (`ingerir_bronze`, `limpiar_silver`, `pipeline.main`)

### Parallel Opportunities

- T007 y T008 (Setup) en paralelo
- T009 y T010 (Foundational) — T010 en paralelo; T009 es prerrequisito de contenido para
  varias tareas posteriores pero no comparte archivo con T010
- Todos los tests `[P]` dentro de una historia en paralelo (archivos distintos)
- T014/T015 (US1), T021/T022/T024 (US2), T026/T027 (US3), T030/T031 (US4) en paralelo
  entre sí dentro de su fase

---

## Parallel Example: User Story 1

```bash
# Lanzar juntos los tests de User Story 1:
Task: "Test unitario de normalizar_nombre/generar_hash_pii en tests/unit/test_pii.py"
Task: "Test unitario de detección de encabezado + lectura acotada en tests/unit/test_excel_reader.py"
Task: "Test de integración de ingestión Bronze en tests/integration/test_ingestion_bronze.py"

# Lanzar juntas las implementaciones de módulos independientes de User Story 1:
Task: "Implementar pii.py en src/covid_analytics/ingestion/pii.py"
Task: "Implementar excel_reader.py en src/covid_analytics/ingestion/excel_reader.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 únicamente)

1. Completar Phase 1: Setup
2. Completar Phase 2: Foundational (CRÍTICO — bloquea todas las historias)
3. Completar Phase 3: User Story 1
4. **DETENER y VALIDAR**: probar User Story 1 de forma independiente (T013 en verde)
5. Esto ya cumple el Principio I (PII) de forma aislada, aunque sin Silver todavía

### Incremental Delivery

1. Setup + Foundational → fundación lista
2. + User Story 1 → validar independientemente → MVP de seguridad de PII
3. + User Story 2 → validar independientemente → Silver limpio (sin cruce)
4. + User Story 3 → validar independientemente → dataset unificado
5. + User Story 4 → validar independientemente → pipeline completo persistido y auditable
6. Phase 7 (Polish) → Guantelete en verde + validación manual contra el Excel real

## Notes

- `[P]` = archivos distintos, sin dependencias pendientes entre sí
- La etiqueta `[Story]` mapea cada tarea a su historia de usuario para trazabilidad
- Verificar que los tests fallan antes de implementar (TDD, Principio IV)
- Ningún test debe abrir el `.xlsx` real con PII — solo `tests/fixtures/excel_sintetico.py`
- Detenerse en cada checkpoint para validar la historia de forma independiente
