# Feature Specification: Dashboard Epidemiológico Interactivo (Streamlit)

**Feature Branch**: `003-dashboard-epidemiologico`

**Created**: 2026-08-19

**Status**: Draft

**Input**: User description: "Feature 003: Dashboard Epidemiológico Interactivo en Streamlit para el Hospital Gustavo Baz. Construir una aplicación web interactiva que consuma únicamente los datasets en `data/gold/*.parquet` sin realizar transformaciones pesadas en tiempo de renderizado: panel de filtros reactivos (fechas, sexo, grupo etario, derechohabiencia), tarjetas KPI, y cinco pestañas (curva epidemiológica, demografía/pirámide, distribución geoespacial, riesgo clínico, calidad/telemetría)."

---

## I. Relación con la Constitución del Proyecto

Esta especificación está gobernada de forma estricta por la **Constitución de COVID-19 Analytics (Hospital Gustavo Baz)** (`.specify/memory/constitution.md`):

1. **Principio I (Privacidad y Anonimización):** El tablero DEBE consumir exclusivamente artefactos ya anonimizados de las capas Silver/Gold (`data/gold/*.parquet` y el reporte de calidad de Silver). Cero acceso a Bronze, cero PII en pantalla, logs o exportaciones.
2. **Principio II (Arquitectura Medallion):** Esta feature toca dos capas: extiende la capa Gold (`src/covid_analytics/analytics/`) con una nueva tabla agregada por derechohabiencia (FR-006a) y una nueva columna `grupo_edad_ui` en `metricas_demografia.parquet` (FR-005a), y añade la capa de presentación (`src/covid_analytics/ui/`), estrictamente downstream de Gold. La UI no implementa lógica de limpieza ni agregaciones analíticas nuevas — toda reagrupación de dimensiones (edad, derechohabiencia) ocurre en Gold, nunca sobre microdatos en tiempo de renderizado.
3. **Principio III (El Guantelete):** El código de UI DEBE aprobar `mypy --strict src`, `ruff check`/`ruff format --check`, y `pytest --cov=src --cov-fail-under=90`, incluyendo smoke tests con `streamlit.testing.v1.AppTest`.
4. **Principio IV (SDD Estricto y TDD):** Claude Code DEBE implementar el tablero mediante TDD estricto partiendo de los contratos y tareas definidos en `plan.md`/`tasks.md` de esta especificación.

---

## Clarifications

### Session 2026-08-19

- Q: Los 14 grupos etarios canónicos de Gold no alinean con los cortes que pide el sidebar (`<18`, `18-39`, `40-59`, `60+`): el bin canónico `36-40` cruza el corte de 40 años y `56-60` cruza el corte de 60 años. ¿Cómo debería resolver la especificación esa desalineación de límites? → A: Extender Gold con una columna exacta — añadir `grupo_edad_ui` a `metricas_demografia.parquet`, calculada con los cortes exactos 18/40/60 desde Silver (FR-005a), sin aproximación ni redondeo.
- Q: FR-004 decía que OTRO/INDETERMINADO "se incluyen sin filtro dedicado" (siempre visibles), pero la Historia 2/Escenario 2 decía que seleccionar solo FEMENINO deja "solo los casos con sexo F" (los excluye). ¿Cuál regla es la correcta? → A: Selección exacta excluye todo lo demás — cualquier selección explícita de sexo (F y/o M) filtra literalmente a esos códigos; OTRO/INDETERMINADO solo aparecen cuando no se aplica ningún filtro de sexo (selección vacía = todas las categorías).
- Q: El caso de borde de "artefactos Gold ausentes" solo cubría la ausencia total. ¿Cómo debe comportarse el tablero si solo falta un archivo Gold (ej. `metricas_derechohabiencia.parquet` antes de reprocesar el pipeline) mientras los demás existen? → A: Degradación por pestaña — el tablero carga con los archivos disponibles; solo la(s) pestaña(s) cuyo archivo falta muestran "no disponible", el resto funciona sin restricción.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Curva Epidemiológica y KPIs Globales (Priority: P1) 🎯 MVP

Como **Vigilante Epidemiológico**, quiero ver una curva de casos diarios con su media móvil de 7 días junto con las tarjetas de KPIs globales (pruebas totales, positivos, tasa de positividad, tasa de hospitalización), filtrable por rango de fechas, para monitorear la tendencia de la pandemia sin depender de scripts o Excel.

**Why this priority**: Es el caso de uso más frecuente y de mayor valor inmediato; reemplaza directamente el flujo manual de `data_analysis.py` y es el único requisito para un MVP demostrable con datos reales.

**Independent Test**: Cargar `series_temporales.parquet` y `kpis_generales.parquet` sintéticos, mover el slider de fechas a un subrango, y verificar que la curva, la media móvil y las 4 tarjetas KPI se recalculan sobre el subrango sin errores ni recarga completa de página.

**Acceptance Scenarios**:

1. **Given** el tablero cargado con datos Gold sintéticos de 30 días, **When** el usuario abre la aplicación sin tocar ningún filtro, **Then** las 4 tarjetas KPI (Total Pruebas, Casos Positivos Confirmados, Tasa Global de Positividad, Tasa de Hospitalización) muestran los valores globales de `kpis_generales.parquet` y la Pestaña 1 muestra la curva completa de 30 días con su media móvil de 7 días.
2. **Given** el tablero cargado, **When** el usuario acota el slider de fechas a los últimos 7 días del rango disponible, **Then** la curva y las tarjetas KPI se recalculan usando únicamente los días seleccionados, sin recargar la página completa.

---

### User Story 2 - Demografía y Pirámide Poblacional (Priority: P2)

Como **Epidemiólogo y Analista de Salud Pública**, quiero una pirámide poblacional interactiva (edad × sexo) y un gráfico de positividad por grupo etario, filtrables por sexo y grupo etario, para identificar rápidamente qué poblaciones concentran mayor riesgo.

**Why this priority**: Segundo caso de uso más solicitado tras la curva; depende únicamente de `metricas_demografia.parquet`, ya disponible desde 002-covid-gold.

**Independent Test**: Cargar `metricas_demografia.parquet` sintético con múltiples grupos etarios y sexos, aplicar el multiselector de sexo a un solo valor, y verificar que la pirámide y las barras de positividad excluyen a los demás sexos.

**Acceptance Scenarios**:

1. **Given** el tablero cargado, **When** el usuario no aplica ningún filtro de sexo o grupo etario, **Then** la Pestaña 2 muestra la pirámide poblacional completa usando las 4 categorías exactas de `grupo_edad_ui` (`<18`, `18-39`, `40-59`, `60+`, FR-005a) y las barras de tasa de positividad por grupo etario.
2. **Given** el tablero cargado, **When** el usuario selecciona únicamente `FEMENINO` en el filtro de sexo, **Then** la pirámide muestra solo la barra femenina por grupo etario y las tarjetas KPI reflejan solo los casos con sexo `F`.

---

### User Story 3 - Distribución Geoespacial (Priority: P2)

Como **Tomador de Decisiones Hospitalario**, quiero un mapa de concentración de casos por municipio, incluyendo la zona de influencia hospitalaria, para priorizar zonas de alta propagación en la planeación de recursos.

**Why this priority**: Complementa la vista territorial ya definida como prioridad P2 en 002-covid-gold; depende únicamente de `distribucion_geografica.parquet` y del shapefile municipal ya referenciado por esa feature.

**Independent Test**: Cargar `distribucion_geografica.parquet` sintético con varios municipios de la zona de influencia (Nezahualcóyotl, Chimalhuacán, La Paz, Ecatepec, Otros), renderizar el mapa, y verificar que cada municipio se colorea según su volumen/tasa de casos sin errores de unión geográfica.

**Acceptance Scenarios**:

1. **Given** el tablero cargado, **When** el usuario abre la Pestaña 3, **Then** se muestra un mapa coroplético/heatmap de México acotado a la zona de influencia hospitalaria, coloreado por volumen o tasa de casos por municipio.
2. **Given** un municipio del dataset sin geometría equivalente en el shapefile, **When** se renderiza el mapa, **Then** ese municipio se omite del mapa (con aviso agregado, no error) sin romper el resto de la visualización.

---

### User Story 4 - Riesgo Clínico por Derechohabiencia (Priority: P3)

Como **Director Médico del Hospital**, quiero cruzar la derechohabiencia de los pacientes con la tasa de hospitalización y el resultado de la prueba, para evaluar si existen brechas de atención según el tipo de afiliación (IMSS, ISSSTE, ISSEMYM, INSABI, privado, ninguna).

**Why this priority**: Valor analítico real pero de menor frecuencia de consulta que la curva o la demografía; además requiere primero extender la capa Gold con la nueva tabla `metricas_derechohabiencia.parquet` (FR-006a).

**Independent Test**: Con `metricas_derechohabiencia.parquet` sintético, filtrar por una derechohabiencia específica y verificar que el gráfico de barras apiladas de la Pestaña 4 muestra únicamente esa afiliación con su desglose de resultado/hospitalización.

**Acceptance Scenarios**:

1. **Given** datos de origen con desglose por derechohabiencia disponibles, **When** el usuario abre la Pestaña 4, **Then** se muestra un gráfico de barras apiladas de derechohabiencia vs. tasa de hospitalización y vs. distribución de resultado de prueba.
2. **Given** el usuario selecciona una sola derechohabiencia en el sidebar, **When** la selección se aplica, **Then** el gráfico y las tarjetas KPI reflejan únicamente esa afiliación.

---

### User Story 5 - Calidad y Telemetría del Pipeline (Priority: P3)

Como **Ingeniero de Datos / Auditor**, quiero ver un resumen del reporte de calidad del pipeline (registros procesados, cruces, huérfanos, correcciones y anomalías de fecha), para confiar en la integridad de lo que el tablero muestra antes de compartirlo.

**Why this priority**: No es analítica clínica, pero es el requisito de transparencia/auditoría que cierra el ciclo de confianza del tablero; depende de un artefacto ya existente (`data_quality_summary.json`).

**Independent Test**: Con un `data_quality_summary.json` sintético, verificar que la Pestaña 5 muestra cada campo del reporte (incluyendo `fechas_anomalas_fuera_ventana`) sin exponer ningún identificador individual.

**Acceptance Scenarios**:

1. **Given** un `data_quality_summary.json` válido presente, **When** el usuario abre la Pestaña 5, **Then** se muestran todas las métricas del reporte (filas leídas, cruces exitosos, huérfanos, correcciones, colisiones, fechas anómalas fuera de ventana, timestamp de ejecución).
2. **Given** `data_quality_summary.json` ausente (pipeline nunca ejecutado), **When** el usuario abre la Pestaña 5, **Then** se muestra un mensaje explicativo de "reporte no disponible" en vez de un error no controlado.

---

### Edge Cases

- **Todos los artefactos Gold ausentes:** Si ningún archivo de `data/gold/*.parquet` existe (pipeline nunca ejecutado), el tablero DEBE mostrar un estado inicial explicativo ("ejecute el pipeline primero") en vez de fallar al iniciar.
- **Artefacto Gold individual ausente:** Si falta un archivo específico (ej. `metricas_derechohabiencia.parquet` no regenerado aún), el tablero DEBE seguir cargando con los archivos disponibles; únicamente la(s) pestaña(s) y tarjetas KPI que dependan del archivo faltante muestran un estado "no disponible", sin afectar al resto del tablero.
- **Combinación de filtros sin resultados:** Si la combinación de fecha/sexo/grupo etario/derechohabiencia no arroja ninguna fila, cada visualización afectada DEBE mostrar un estado "sin datos para esta selección" en vez de un gráfico vacío o un traceback.
- **Deselección total de un multiselector:** Si el usuario deselecciona todas las opciones de un filtro multiselección (sexo o grupo etario), el sistema lo trata como "sin filtro aplicado" — se muestran todas las categorías disponibles, incluyendo aquellas sin opción dedicada en el sidebar (ej. `OTRO`/`INDETERMINADO` en sexo) — nunca como "cero resultados".
- **Reporte de calidad ausente o corrupto:** Ver User Story 5, Acceptance Scenario 2.
- **Municipio sin geometría:** Ver User Story 3, Acceptance Scenario 2.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Dashboard - Carga y Caché):** El sistema DEBE cargar `metricas_demografia.parquet`, `series_temporales.parquet`, `distribucion_geografica.parquet`, `kpis_generales.parquet` y `metricas_derechohabiencia.parquet` (FR-006a) desde `data/gold/` usando un mecanismo de caché en memoria por sesión, evitando releer disco en cada interacción de filtro.
- **FR-002 (Dashboard - Privacidad):** El sistema NO DEBE leer, en ningún momento, artefactos de la capa Bronze ni columnas con identificadores individuales de paciente. La única excepción explícita es `data/silver/data_quality_summary.json` (telemetría agregada sin PII, contrato ya validado en 001-covid-etl), consumido únicamente por la Pestaña 5.
- **FR-003 (Dashboard - Filtro de Fechas):** El sistema DEBE ofrecer un control de rango de fechas acotado al mínimo y máximo realmente presentes en `series_temporales.parquet` dentro de la ventana epidemiológica `[2020-01-01, 2023-12-31]`.
- **FR-004 (Dashboard - Filtro de Sexo):** El sistema DEBE ofrecer un selector de selección múltiple con las etiquetas `MASCULINO`/`FEMENINO`, mapeadas a los códigos canónicos `M`/`F` de la capa Gold. El filtro es de coincidencia exacta: si el usuario selecciona uno o ambos valores, solo esos códigos se muestran (excluyendo `OTRO`/`INDETERMINADO`); si no selecciona ninguno (ver Edge Cases, "Deselección total"), se muestran todas las categorías, incluyendo `OTRO`/`INDETERMINADO` agregadas como "Otro/Indeterminado" donde aplique.
- **FR-005 (Dashboard - Filtro de Grupo Etario):** El sistema DEBE ofrecer un selector de selección múltiple con las 4 categorías exactas `<18`, `18-39`, `40-59`, `60+`, leyendo la columna `grupo_edad_ui` de `metricas_demografia.parquet` (FR-005a) — sin aproximación por redondeo de los bins canónicos.
- **FR-005a (Gold - Columna `grupo_edad_ui`):** `metricas_demografia.parquet` (002-covid-gold) DEBE extenderse con una columna adicional `grupo_edad_ui` (`<18` | `18-39` | `40-59` | `60+` | `SIN_DATO`), calculada en la capa Gold directamente desde `edad` de `data/silver/casos_unificados.parquet` con los cortes exactos en 18, 40 y 60 años — no derivada de los 14 grupos etarios canónicos (`grupo_edad`), cuyos bins `36-40` y `56-60` cruzan esos cortes y producirían clasificación incorrecta. Ambas columnas (`grupo_edad` y `grupo_edad_ui`) coexisten en la misma tabla.
- **FR-006 (Dashboard - Filtro de Derechohabiencia):** El sistema DEBE ofrecer un selector de derechohabiencia (`IMSS`, `ISSSTE`, `ISSEMYM`, `INSABI`, `PRIVADO`, `NINGUNA`) que filtre las tarjetas KPI y la Pestaña 4, leyendo la nueva tabla `metricas_derechohabiencia.parquet` (FR-006a).
- **FR-006a (Gold - Extensión por Derechohabiencia):** La capa Gold (`src/covid_analytics/analytics/`) DEBE extenderse con una nueva tabla `data/gold/metricas_derechohabiencia.parquet`, agregada por `(derechohabiencia, resultado_prueba, estatus_paciente)` a partir de `data/silver/casos_unificados.parquet`, con columnas `total_casos`, `porcentaje_del_total`, `tasa_positividad_grupo`, `tasa_hospitalizacion_grupo` y `tasa_letalidad_grupo` (mismas fórmulas y protección de división por cero que `metricas_demografia.parquet`, 002-covid-gold). Como `derechohabiencia` es texto libre en Silver (sentinel `"NINGUNO"`, sin catálogo cerrado), esta tabla DEBE estandarizarla al catálogo `IMSS`, `ISSSTE`, `ISSEMYM`, `INSABI`, `PRIVADO`, `NINGUNA`, agrupando cualquier otro valor observado (ej. `SEDENA`, variantes de captura) en una categoría `OTRA`, preservando la consistencia marginal exacta (suma de `total_casos` = filas de Silver) exigida por FR-007 de 002-covid-gold.
- **FR-007 (Dashboard - Tarjetas KPI):** El sistema DEBE mostrar 4 métricas (Total Pruebas, Casos Positivos Confirmados, Tasa Global de Positividad, Tasa de Hospitalización), recalculadas sobre el subconjunto de datos Gold que resulte de aplicar los filtros activos.
- **FR-008 (Dashboard - Curva Epidemiológica):** El sistema DEBE mostrar, en la Pestaña 1, una serie de tiempo interactiva de casos diarios y su media móvil de 7 días, acotada al rango de fechas seleccionado.
- **FR-009 (Dashboard - Demografía y Pirámide):** El sistema DEBE mostrar, en la Pestaña 2, una pirámide poblacional (edad × sexo) y un gráfico de tasa de positividad por grupo etario, ambos reactivos a los filtros de sexo y grupo etario.
- **FR-010 (Dashboard - Distribución Geoespacial):** El sistema DEBE mostrar, en la Pestaña 3, un mapa de concentración de casos por municipio dentro de la zona de influencia hospitalaria, coloreado por volumen o tasa de casos.
- **FR-011 (Dashboard - Riesgo Clínico):** El sistema DEBE mostrar, en la Pestaña 4, un gráfico de barras apiladas de derechohabiencia vs. tasa de hospitalización y vs. distribución de resultado de prueba, usando `metricas_derechohabiencia.parquet` (FR-006a) como fuente.
- **FR-012 (Dashboard - Calidad y Telemetría):** El sistema DEBE mostrar, en la Pestaña 5, el contenido íntegro de `data_quality_summary.json`, con manejo explícito de archivo ausente (ver Edge Cases).
- **FR-013 (Dashboard - Estados Vacíos):** El sistema DEBE manejar de forma explícita (sin excepciones no controladas) tanto la ausencia total de artefactos Gold como la ausencia de un archivo individual (degradación por pestaña, sin afectar al resto del tablero) y las combinaciones de filtro sin resultados (ver Edge Cases).
- **FR-014 (Dashboard - Tipado y Calidad):** Todos los módulos de `src/covid_analytics/ui/` DEBEN aprobar el Guantelete (`mypy --strict`, `ruff`, `pytest >= 90%` con smoke tests de `AppTest`).

### Key Entities

- **FiltroTablero:** Estado efímero de sesión (rango de fechas, sexos, grupos etarios UI y derechohabiencias seleccionados) que acota todas las vistas; nunca se persiste a disco.
- **VistaKPI:** Las 4 métricas resumen mostradas en las tarjetas, derivadas de `kpis_generales.parquet`/`series_temporales.parquet` tras aplicar `FiltroTablero`.
- **ReporteCalidad:** Representación en pantalla de `data_quality_summary.json` (entidad `ResumenCalidad` ya definida en 001-covid-etl).
- **MetricasDerechohabienciaGold (nueva, FR-006a):** Cubo agregado por `(derechohabiencia, resultado_prueba, estatus_paciente)`, con conteos, porcentaje del total y tasas de positividad/hospitalización/letalidad por grupo — extiende la capa Gold de 002-covid-gold.
- **MetricasDemografiaGold (extendida, FR-005a):** Se le añade la columna `grupo_edad_ui` (`<18`/`18-39`/`40-59`/`60+`/`SIN_DATO`), calculada con cortes exactos, coexistiendo con la columna `grupo_edad` (14 bins canónicos) ya definida en 002-covid-gold.
- *(Las demás entidades de datos subyacentes — `SeriesTemporalesGold`, `DistribucionGeograficaGold`, `KpisGeneralesGold` — ya están definidas en 002-covid-gold y no se redefinen aquí.)*

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001:** Un usuario sin capacitación previa puede identificar la tendencia de casos positivos de las últimas semanas en menos de 30 segundos desde que abre el tablero.
- **SC-002:** Cambiar cualquier filtro del panel lateral actualiza todas las visualizaciones soportadas por ese filtro en menos de 2 segundos, sin recargar la página completa.
- **SC-003:** La carga inicial del tablero completo (KPIs + 5 pestañas) toma menos de 5 segundos en un entorno local estándar con los volúmenes de datos típicos del hospital.
- **SC-004:** 100% de las visualizaciones y artefactos mostrados provienen exclusivamente de datos agregados (capa Gold) o del reporte de calidad de Silver — cero columnas o valores individuales de paciente visibles en pantalla, exportación o logs.
- **SC-005:** El tablero permanece utilizable (sin pantallas en blanco ni errores no controlados) ante artefactos Gold ausentes o combinaciones de filtro sin resultados, mostrando siempre un estado explícito.

---

## Assumptions

- **Nombres reales de archivo:** El tablero consume los nombres de archivo ya definidos y persistidos por 002-covid-gold (`metricas_demografia.parquet`, `series_temporales.parquet`, `distribucion_geografica.parquet`, `kpis_generales.parquet`) más la nueva `metricas_derechohabiencia.parquet` (FR-006a) — no `gold_*.parquet` como sugería la descripción informal de la feature.
- **Catálogo de derechohabiencia:** `derechohabiencia` es texto libre en la capa Silver (sin catálogo cerrado, solo el sentinel `"NINGUNO"`). FR-006a decide estandarizarla al catálogo de 6 categorías pedido por el sidebar (`IMSS`, `ISSSTE`, `ISSEMYM`, `INSABI`, `PRIVADO`, `NINGUNA`) más una categoría `OTRA` para cualquier valor no reconocido (ej. `SEDENA`, variantes de captura), análogo al tratamiento de `municipio_residencia`→`"OTROS"` en 001/002-covid-etl.
- **Excepción de Silver para calidad:** `data/silver/data_quality_summary.json` se trata como entrada explícitamente permitida para la Pestaña 5, pese a que no vive en `data/gold/`, porque no existe un equivalente de telemetría en la capa Gold y el contrato ya garantiza cero PII (001-covid-etl).
- **Grupos etarios de UI:** Los 4 buckets `<18`, `18-39`, `40-59`, `60+` se calculan en Gold como columna independiente `grupo_edad_ui` (FR-005a), no por redondeo de los 14 bins canónicos — evita el error de clasificación que introduciría un mapeo aproximado en los bins `36-40` y `56-60`, que cruzan los cortes de 40 y 60 años. `SIN_DATO` se excluye de la pirámide pero se muestra en un conteo aparte visible en la UI.
- **Geografía:** El mapa reutiliza el shapefile ya referenciado por 002-covid-gold (`mapa_mexico/Division_Municipal_Mexico_2010.shp`) para el join por `municipio_residencia`; no se requiere una nueva fuente geográfica.
- **Zona de influencia hospitalaria:** Se refiere al mismo conjunto de municipios ya usado como ejemplo en 001/002 (Nezahualcóyotl, Chimalhuacán, La Paz, Ecatepec, Otros).
- **Alcance de sesión:** El tablero es de un solo usuario/sesión local, sin autenticación ni roles ni persistencia de filtros entre sesiones, consistente con el alcance actual del proyecto (herramienta interna del hospital).
- **Sin exportación de datos:** Esta feature no incluye descarga/exportación de los datos filtrados (CSV, PDF, etc.); queda fuera de alcance para v1.
