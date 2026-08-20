# Feature Specification: Capa Gold de Analítica y Agregaciones Epidemiológicas

**Feature Branch**: `002-covid-gold`

**Created**: 2026-08-19

**Status**: Draft

**Input**: User description: "Genera la spec de la capa gold, por favor. Agregaciones epidemiológicas, series de tiempo, cortes demográficos, distribución geográfica y métricas clínicas sobre la capa Silver."

---

## I. Relación con la Constitución del Proyecto

Esta especificación está gobernada de forma estricta por la **Constitución de COVID-19 Analytics (Hospital Gustavo Baz)** (`.specify/memory/constitution.md`):

1. **Principio I (Privacidad y Anonimización):** Cero PII en capa Gold. Las tablas agregadas y matriciales operan exclusivamente a nivel de cohortes anonimizadas o sobre el identificador seudonimizado `paciente_id`. Cero nombres, teléfonos o domicilios en reportes o logs.
2. **Principio II (Arquitectura Medallion):** La lógica analítica se implementará exclusivamente en `src/covid_analytics/analytics/` (capa Gold), consumiendo como entrada inmutable `data/silver/casos_unificados.parquet` producida por la capa Silver (`src/covid_analytics/cleaning/`).
3. **Principio III (El Guantelete):** Todo el código analítico DEBE aprobar `mypy --strict src`, `ruff check src tests`, `ruff format --check src tests`, y `pytest --cov=src --cov-fail-under=90`. Pruebas con fixtures sintéticos generados programáticamente.
4. **Principio IV (SDD Estricto y TDD):** Claude Code DEBE implementar los módulos mediante TDD estricto partiendo de los contratos y tareas definidos en esta especificación.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agregaciones Demográficas y de Positividad Multidimensional (Priority: P1) 🎯 MVP

Como **Epidemiólogo y Analista de Salud Pública**, quiero obtener tablas analíticas agregadas por grupos etarios estandarizados, sexo biológico y resultado de prueba, para calcular de manera inmediata tasas de positividad y matrices de incidencia sin reprocesar los microdatos crudos.

**Why this priority**: Reemplaza más de 20 rutinas de filtrado y conteo manual del legacy (`data_analysis.py`), proporcionando el cubo analítico central (Demografía × Resultado × Estatus) necesario para todos los reportes clínicos y tableros.

**Independent Test**: Probar alimentando un dataset Silver sintético con casos en distintos rangos etarios y sexos, verificando que la tabla `metricas_demografia.parquet` calcule con exactitud los conteos agregados, tasas de positividad por grupo y porcentajes de distribución sin pérdida de consistencia matemática.

**Acceptance Scenarios**:

1. **Given** un dataset Silver con pacientes clasificados en `F`, `M`, `OTRO`, `INDETERMINADO` y edades continuas,  
   **When** se ejecuta el motor de agregación demográfica en `src/covid_analytics/analytics/demografia.py`,  
   **Then** se generan grupos etarios normalizados (`0-1`, `2-11`, `12-17`, `18-24`, `25-30`, `31-35`, `36-40`, `41-45`, `46-50`, `51-55`, `56-60`, `61-65`, `66+`, `SIN_DATO`) y se calcula la matriz cruzada de conteos por `resultado_prueba` y `estatus_paciente`.
2. **Given** una cohorte con 100 pruebas concluyentes (70 negativas, 30 positivas) y 10 pendientes,  
   **When** se calcula la tasa de positividad,  
   **Then** el resultado es exactamente `0.30` (30.0%), excluyendo las pruebas pendientes o no concluyentes del denominador de positividad efectiva.

---

### User Story 2 - Series Temporales y Curvas Epidemiológicas (Priority: P2)

Como **Vigilante Epidemiológico**, quiero disponer de agregaciones de frecuencia diaria y semanal con medias móviles de 7 días para las fechas de notificación, toma de muestra, resultado e ingreso hospitalario, para modelar la dinámica de transmisión y el rezago diagnóstico (lags) durante la pandemia.

**Why this priority**: Permite construir curvas epidémicas confiables y evaluar los cuellos de botella temporales en la atención hospitalaria.

**Independent Test**: Alimentar un conjunto de casos sintéticos distribuidos a lo largo de un rango de 30 días, verificando que `series_temporales.parquet` genere una fila por cada fecha del calendario continuo (rellenando días con cero casos), calcule correctamente la media móvil de 7 días y compute los días promedio de rezago.

**Acceptance Scenarios**:

1. **Given** registros Silver con `fecha_notificacion`, `fecha_toma_muestra` y `fecha_resultado`,  
   **When** se genera el dataset de series de tiempo en `src/covid_analytics/analytics/series_tiempo.py`,  
   **Then** se crea una serie temporal diaria completa con métricas de `casos_nuevos_totales`, `casos_positivos`, `media_movil_7d_positivos` y `casos_acumulados`.
2. **Given** registros con fechas faltantes o `NaT`,  
   **When** se procesan las series de tiempo,  
   **Then** se aíslan en una métrica de telemetría de casos sin fecha sin romper la continuidad del índice temporal.
3. **Given** registros unificados con `fecha_notificacion` y `fecha_ingreso_hospital`,  
   **When** se procesan los tiempos de atención,  
   **Then** se calcula la mediana y percentiles (p25, p75) del desfase en días (`dias_entre_notificacion_e_ingreso`).

---

### User Story 3 - Distribución Geográfica y Tasas Municipales (Priority: P2)

Como **Tomador de Decisiones Hospitalario**, quiero métricas agregadas por municipio de residencia (casos totales, confirmados, defunciones, tasas de letalidad y hospitalización), para alimentar mapas temáticos coropléticos y priorizar zonas de alta propagación.

**Why this priority**: Esencial para la toma de decisiones territoriales y la integración directa con los shapefiles vectoriales de `mapa_mexico/Division_Municipal_Mexico_2010.shp`.

**Independent Test**: Verificar que al agregar los datos por `municipio_residencia`, se genere la tabla `distribucion_geografica.parquet` con el total de municipios analizados, tasa de letalidad (`defunciones / positivos`) y tasa de hospitalización (`hospitalizados / positivos`), con manejo seguro de divisiones por cero.

**Acceptance Scenarios**:

1. **Given** casos Silver agrupados en municipios de la zona de influencia (ej. `NEZAHUALCOYOTL`, `CHIMALHUACAN`, `LA PAZ`, `ECATEPEC`, `OTROS`),  
   **When** se ejecuta la agregación geográfica en `src/covid_analytics/analytics/geografia.py`,  
   **Then** se generan métricas consolidadas por municipio incluyendo `tasa_letalidad`, `tasa_hospitalizacion` y `tasa_positividad`.
2. **Given** un municipio con 0 casos positivos,  
   **When** se computa la tasa de letalidad,  
   **Then** la tasa se registra de forma segura como `0.0` en lugar de `NaN` o `Inf`.

---

### User Story 4 - Resumen Ejecutivo y KPIs Generales (Priority: P3)

Como **Director Médico del Hospital**, quiero una vista consolidada de KPIs globales (`kpis_generales.parquet` y `resumen_ejecutivo.json`) que resuma en una sola ficha ejecutiva el volumen total de pacientes, tasa global de letalidad, tasa global de hospitalización, distribución por derechohabiencia y desglose general de resultados.

**Why this priority**: Proporciona el punto de entrada sintético de alto nivel para tableros ejecutivos y resúmenes de prensa médica sin requerir consultas sobre tablas analíticas detalladas.

**Independent Test**: Ejecutar la orquestación analítica completa y verificar que `kpis_generales.parquet` y `data/gold/resumen_ejecutivo.json` contengan todos los indicadores globales con valores consistentes con la suma de las tablas de detalle.

**Acceptance Scenarios**:

1. **When** se ejecuta el pipeline analítico completo (`covid-analytics --layer gold` o módulo `analytics`),  
   **Then** se exportan todas las tablas Gold a `data/gold/` en formato Apache Parquet (Snappy) y se genera `data/gold/resumen_ejecutivo.json`.
2. **When** se comparan las sumatorias de casos positivos entre `kpis_generales`, `metricas_demografia`, `series_temporales` y `distribucion_geografica`,  
   **Then** existe coincidencia aritmética exacta (cero discrepancias en conteos marginales).

---

### Edge Cases

- **Cohortes Vacías en Grupos Etarios:** Si para un rango de edad (ej. `0-1`) no hay ningún registro en el dataset, el cubo analítico debe preservar la categoría con conteos en `0` y tasas en `0.0` para garantizar estabilidad de esquemas en consumidores de visualización.
- **Fechas Fuera de Rango o Invertidas:** Si una fecha de resultado es anterior a la fecha de toma de muestra, el motor analítico debe registrar la anomalía en las métricas de calidad y calcular los lags como valores nulos sin abortar el pipeline.
- **División por Cero en Tasas:** Cualquier cálculo de ratio o porcentaje cuyo denominador sea 0 (`total_pruebas = 0` o `positivos = 0`) debe retornar `0.0` de forma determinista.
- **Pacientes con Múltiples Registros o Huérfanos:** Los registros con `es_registro_unificado = False` deben considerarse en los análisis de casos ambulatorios o nominales según corresponda sin duplicar conteos globales.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Gold - Entrada):** El módulo analítico DEBE leer como fuente primaria `data/silver/casos_unificados.parquet` validando la conformidad con el contrato de la capa Silver.
- **FR-002 (Gold - Rangos Etarios Canónicos):** Se DEBE implementar la función de categorización etaria con los siguientes 14 intervalos cerrados:
  `['0-1', '2-11', '12-17', '18-24', '25-30', '31-35', '36-40', '41-45', '46-50', '51-55', '56-60', '61-65', '66+', 'SIN_DATO']`, asignando `SIN_DATO` a cualquier registro con edad `-1.0` o nula.
- **FR-003 (Gold - Positividad y Severidad):** Se DEBEN calcular las siguientes métricas epidemiológicas canónicas:
  $$\text{Tasa Positividad} = \frac{\text{POSITIVOS}}{\text{POSITIVOS} + \text{NEGATIVOS}}$$
  $$\text{Tasa Letalidad (CFR)} = \frac{\text{DEFUNCION (en POSITIVOS)}}{\text{TOTAL POSITIVOS}}$$
  $$\text{Tasa Hospitalización} = \frac{\text{HOSPITALIZADO (en POSITIVOS)}}{\text{TOTAL POSITIVOS}}$$
- **FR-004 (Gold - Series Temporales Continuas):** Las series temporales DEBEN generar un índice continuo diario entre la fecha mínima y máxima observada, rellenando con ceros los días sin actividad y calculando medias móviles centradas o retrospectivas a 7 días (`window=7, min_periods=1`).
- **FR-004a (Gold - Anomalías de Fechas Invertidas):** Cuando `fecha_resultado` sea anterior a `fecha_toma_muestra` (o análogamente `fecha_ingreso_hospital` anterior a `fecha_notificacion`), el motor de series temporales DEBE calcular el lag correspondiente como valor nulo, registrar el conteo de la anomalía en una métrica de telemetría (`casos_fechas_invertidas`) expuesta junto a `series_temporales.parquet`, y continuar el procesamiento sin abortar el pipeline (ver Edge Case "Fechas Fuera de Rango o Invertidas").
- **FR-005 (Gold - Geografía):** El dataset geográfico DEBE agregar a nivel de `municipio_residencia`, computando volumen de casos, positivos, defunciones, hospitalizados y tasas asociadas.
- **FR-006 (Gold - Formato y Persistencia):** Todas las tablas de la capa Gold DEBEN persistirse en el directorio `data/gold/` en formato Apache Parquet con compresión `snappy` utilizando `pyarrow`.
- **FR-007 (Gold - Integridad Estadística):** La suma marginal de casos de cada tabla analítica Gold DEBE ser idéntica al número total de filas válidas del dataset Silver origen.
- **FR-008 (Gold - Tipado y Calidad):** Todos los módulos de `src/covid_analytics/analytics/` DEBEN aprobar el Guantelete (`mypy --strict`, `ruff`, `pytest >= 90%` con fixtures sintéticos).

### Key Entities

- **MetricasDemografiaGold:** Entidad columnar que agrega la interacción entre grupo etario, sexo, resultado de prueba y estatus del paciente, con conteos y porcentajes de prevalencia.
- **SeriesTemporalesGold:** Entidad columnar temporal indexada por fecha con conteos diarios, acumulados y medias móviles de 7 días por evento clínico (notificación, toma de muestra, resultado, ingreso).
- **DistribucionGeograficaGold:** Entidad columnar territorial por municipio de residencia con métricas de volumen, positividad, letalidad y hospitalización.
- **KpisGeneralesGold:** Entidad escalar/unifila que resume los grandes agregados epidemiológicos del hospital y la red negativa.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Privacidad Cero PII):** 100% de las tablas y artefactos generados en `data/gold/` contienen cero columnas PII y cero datos personales individuales.
- **SC-002 (Consistencia Aritmética):** 100% de coherencia matemática entre las tablas Gold (las sumas de casos de todas las tablas coinciden exactamente con el dataset Silver de entrada).
- **SC-003 (Rendimiento y Persistencia):** La generación completa de todas las tablas Gold a partir del archivo Silver toma menos de 5 segundos en ejecución local estándar.
- **SC-004 (El Guantelete en Verde):**
  - `mypy --strict src` en estado verde (cero errores de tipado).
  - `ruff check src tests` y `ruff format --check src tests` limpios.
  - `pytest --cov=src --cov-fail-under=90` pasando con fixtures sintéticos al 100%.

---

## Assumptions

- **Disponibilidad de Capa Silver:** Se asume que `data/silver/casos_unificados.parquet` existe y cumple estrictamente con el esquema definido en `specs/001-covid-etl/contracts/casos_unificados_silver.md`.
- **Definición de Denominadores Epidemiológicos:** Para el cálculo de positividad, se toma como denominador únicamente las pruebas con resultado definitivo (`POSITIVO + NEGATIVO`), excluyendo pruebas con estatus `PENDIENTE` o `NO_CONCLUYENTE`, siguiendo la norma técnica de vigilancia epidemiológica.
- **Compatibilidad con Visualizadores y GIS:** La estructura de `distribucion_geografica.parquet` utiliza nombres estandarizados de municipios compatibles para realizar joins directos con `mapa_mexico/Division_Municipal_Mexico_2010.dbf` / `.shp`.
