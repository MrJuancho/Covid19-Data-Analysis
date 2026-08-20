# Feature Specification: Pipeline ETL de COVID-19 (Bronze a Silver)

**Feature Branch**: `001-covid-etl`

**Created**: 2026-08-19

**Status**: Draft

**Input**: User description: "Ingesta Bronze, Limpieza Silver, Almacenamiento Parquet, Contratos Pydantic/Pandas y Cruce Seguimiento↔Nominal"

---

## I. Relación con la Constitución del Proyecto

Esta especificación está gobernada por la **Constitución de COVID-19 Analytics (Hospital Gustavo Baz)**. Todos los entregables, diseños de código y pruebas descritos a continuación DEBEN alinearse de forma no negociable con los siguientes principios:

1. **Principio I (Privacidad y Anonimización):** Se prohíbe escribir o persistir cualquier dato PII (`CASO`, `NOMBRE DEL PACIENTE`, `CALLE`, `TELEFONO`, etc.) en texto plano fuera de la capa Bronze. Toda persistencia en Silver o superior usará el hash de seudonimización canónico.
2. **Principio II (Arquitectura por Capas):** La ingesta se implementará estrictamente en `src/covid_analytics/ingestion/` (capa Bronze) y la normalización/cruce en `src/covid_analytics/cleaning/` (capa Silver).
3. **Principio III (El Guantelete):** El código final DEBE superar de forma automatizada `mypy --strict`, `ruff check`, y `pytest --cov=src --cov-fail-under=90`. Las pruebas unitarias usarán exclusivamente fixtures de datos sintéticos generados programáticamente.
4. **Principio IV (SDD Estricto):** Esta especificación es un prerrequisito obligatorio antes de generar planes y tareas de implementación.

---

## User Scenarios &amp; Testing *(mandatory)*

### User Story 1 - Ingesta Bronze Segura y Anonimización de PII (Priority: P1)

Como **Ingeniero de Datos**, quiero ingerir las hojas de datos del Excel de forma segura en memoria y aplicar seudonimización inmediata a los campos PII, para garantizar que la información personal de los pacientes nunca llegue a disco ni a los módulos analíticos en texto plano.

**Why this priority**: Es el núcleo de seguridad exigido por el **Principio I** de la Constitución. Mitiga además la fuga de memoria y asegura el cumplimiento legal de protección de datos de salud desde el primer paso del pipeline.

**Independent Test**: Se puede probar de forma aislada alimentando un Excel sintético con columnas con nombres reales y verificando que el DataFrame resultante de la fase Bronze tenga la columna `paciente_id` hasheada y que no existan las columnas de nombres originales ni direcciones en texto plano en la salida.

**Acceptance Scenarios**:

1. **Given** un archivo de Excel con la hoja `SEGUIMIENTO DE CASOS COVID 19` que contiene nombres en `CASO` y enteros en `NO. (consecutivo)`,  
 **When** se ejecuta la ingesta en `src/covid_analytics/ingestion/`,  
 **Then** se genera una columna `paciente_id` aplicando un hash `SHA-256(Nombre_Normalizado + Folio + Sal)` donde el Folio es `NO. (consecutivo)`, y las columnas originales de PII se eliminan completamente.
2. **Given** un archivo de Excel con formato de celdas inflado artificialmente (hasta 1,000,000 de filas fantasma),  
 **When** el módulo de ingesta lee las hojas,  
 **Then** se limita la lectura a través de `usecols` y un mecanismo de terminación temprana para filas vacías, consumiendo menos de 500 MB de RAM.

---

### User Story 2 - Limpieza y Normalización Semántica Silver (Priority: P2)

Como **Analista de Datos**, quiero que los campos demográficos (Edad y Sexo), fechas polimórficas y categorías de derechohabiencia y municipio de residencia estén normalizados a un catálogo canónico, para poder realizar agregaciones estadísticas libres de duplicados y errores de captura.

**Why this priority**: El legacy audit revela múltiples inconsistencias de captura (fechas en columnas de resultado, edades en días/meses no numéricas, duplicados de acentos, y columnas de edad cruzadas por sexo). Este paso limpia las inconsistencias antes de consolidar la información.

**Independent Test**: Alimentar la lógica de limpieza de `src/covid_analytics/cleaning/` con vectores que incluyan edades como `"RN"`, `"3M"`, `"años: 4"`, fechas seriales de Excel (`43908`), strings de fecha mezclados con texto (`'24/03/2020  H. ZUMPANGO'`) y campos con sexo/edad intercambiados, y verificar que la salida de Pandas cumpla estrictamente los tipos de la especificación.

**Acceptance Scenarios**:

1. **Given** un registro en Nominal con columnas `EDAD | F` y `EDAD | M` desanidadas,  
 **When** pasa por el proceso de limpieza demográfica,  
 **Then** se consolidan en una sola columna numérica `edad` y una columna categórica `sexo` (`F` o `M`).
2. **Given** una fecha almacenada como el string `'24/03/2020  H. ZUMPANGO'` o el número serial de Excel `43908`,  
 **When** el parser de fechas polimórficas la procesa,  
 **Then** retorna un tipo datetime correspondiente al `2020-03-24` de forma consistente.
3. **Given** un registro de Seguimiento donde `RESULTADO` tiene una fecha válida (ej. `2020-09-03`) y `FECHA DE RESULTADO` tiene un string categórico (ej. `POSITIVO`),  
 **When** se ejecuta el corrector de columnas intercambiadas,  
 **Then** los valores se intercambian a sus columnas lógicas correctas antes de la normalización.

---

### User Story 3 - Cruce Heurístico de Seguimiento y Hospitalizados (Priority: P2)

Como **Epidemiólogo**, quiero relacionar los registros del seguimiento ambulatorio con sus admisiones hospitalarias nominales aun cuando no exista un folio físico idéntico entre ambos, para reconstruir de forma integrada el viaje clínico del paciente.

**Why this priority**: La auditoría legacy demostró que no existe una columna `folio` en común en más del 99% de las filas. Vincular las dos hojas mediante una llave sintética y proximidad temporal es la única manera de unificar el dataset.

**Independent Test**: Generar un conjunto sintético con un paciente que tiene un registro ambulatorio notificado el `2020-03-18` y un registro de ingreso en Nominal del `2020-03-22`. Verificar que se unifiquen en una sola fila consolidada con ambas fechas y estatus final `HOSPITALIZADO`.

**Acceptance Scenarios**:

1. **Given** un registro en Seguimiento y otro en Nominal con el mismo `paciente_id` (mismo hash de nombre + folio + sal), misma edad y mismo sexo, con fechas de notificación e ingreso separadas por $\le 7$ días,  
 **When** se ejecuta el merge de capas en `src/covid_analytics/cleaning/`,  
 **Then** se fusionan en un único registro unificado que consolida ambas trayectorias.
2. **Given** registros con el mismo `paciente_id` pero cuyas fechas de notificación e ingreso difieren por más de 7 días,  
 **When** se realiza el cruce,  
 **Then** el sistema los procesa como registros independientes (huérfanos clínicos) para evitar fusiones incorrectas de contagios distantes en el tiempo.

---

### User Story 4 - Persistencia de Capa Silver y Telemetría de Calidad (Priority: P3)

Como **Administrador del Sistema de Datos**, quiero almacenar los datos limpios en un formato altamente optimizado y disponer de un resumen JSON con métricas de calidad de la ejecución, para auditar y asegurar que el pipeline opera dentro de límites sanos de error.

**Why this priority**: Permite alimentar de manera eficiente las capas Gold analíticas y proporciona observabilidad automatizada sobre errores de ingesta y volumen de anonimización.

**Independent Test**: Verificar mediante scripts automatizados que al concluir la ejecución del pipeline completo, el archivo Parquet destino se escriba correctamente y que el JSON de métricas contenga campos numéricos positivos y ninguna métrica en nulo.

**Acceptance Scenarios**:

1. **When** el pipeline finaliza con éxito,  
 **Then** escribe el dataset unificado en `data/silver/casos_unificados.parquet` utilizando compresión Snappy y guardando de forma explícita el esquema de tipos lógicos de Pandas.
2. **When** se procesan los datos a través del pipeline,  
 **Then** se escribe en `data_quality_summary.json` un reporte detallando filas leídas en Bronze, registros hasheados, cruces exitosos, correcciones de columnas intercambiadas y porcentaje de registros huérfanos.

---

### Edge Cases

- **Ausencia de Folio en la Ingesta:** Si la columna `NO. (consecutivo)` o `NO.` es nula o inválida, el generador de hash PII debe lanzar una advertencia y usar una cadena vacía o una máscara determinista para el campo `Folio` en la concatenación de la llave `SHA-256(Nombre_Normalizado + Folio + Sal)` para no bloquear la ingesta.
- **Valores Nulos Extremos en Demográficos:** Si tanto `EDAD | F` como `EDAD | M` son nulos en un registro de hospitalizados, se debe asignar la edad por defecto `-1.0` y sexo `INDETERMINADO` para permitir el almacenamiento de la ficha clínica sin romper la restricción de tipo numérico.
- **Colisiones en Llave Sintética Heurística:** Si un paciente homónimo (mismo hash) tiene múltiples admisiones en el mismo hospital durante el mismo rango temporal, el algoritmo de cruce debe asociar el registro con menor diferencia de días absoluta ($|\Delta t|$) y registrar la colisión en las métricas de calidad.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Bronze):** El pipeline DEBE leer las hojas `RED NEGATIVA`, `SEGUIMIENTO DE CASOS COVID 19` y  `NOMINAL DE HOSPITALIZADOS` localizando los encabezados mediante búsquedas de palabras clave en lugar de índices fijos de fila (`skiprows` estático).
- **FR-002 (Bronze - Privacidad):** El pipeline DEBE transformar de forma inmediata las columnas `CASO` y `NOMBRE DEL PACIENTE` en el campo unificado `paciente_id` aplicando un hash criptográfico `SHA-256` utilizando la siguiente fórmula:
  $$
  \text{paciente\_id} = \text{SHA256}(\text{Normalizar}(\text{Nombre}) + \text{str}(\text{Folio}) + \text{Sal})
  $$
  Donde `Normalizar()` remueve acentos, mayúsculas y espacios duplicados, `Folio` corresponde al número consecutivo de la hoja de origen, y `Sal` se extrae de la variable de entorno `COVID_PII_SALT`.
- **FR-003 (Bronze - Seguridad):** Las columnas originales con datos en texto plano de `CASO`, `NOMBRE DEL PACIENTE`, `CALLE`, `TELEFONO` y direcciones DEBEN ser eliminadas del DataFrame inmediatamente después de generar el hash y no deben ser escritas en disco en la capa Bronze.
- **FR-004 (Silver - Demografía):** El pipeline DEBE unificar las columnas `EDAD | F` y `EDAD | M` de la hoja Nominal en un campo numérico `edad` de tipo `float64` y un campo categórico `sexo` (`F`/`M`/`OTRO`/`INDETERMINADO`).
- **FR-005 (Silver - Fechas):** Se DEBE implementar un parser de fechas polimórfico que reconozca objetos datetime, strings estructurados (`DD/MM/YYYY`), strings con texto adicional (ej. `'24/03/2020  H. ZUMPANGO'`) y enteros representativos de seriales de Excel, retornando `NaT` para valores clínicos no-fecha como `"PENDIENTE"`.
- **FR-006 (Silver - Estandarización):** El pipeline DEBE estandarizar la columna `municipio_residencia` utilizando un catálogo explícito de equivalencias (mapeo directo de nombres) en lugar de filtros regex amplios e imprecisos. Las residencias no identificadas se clasificarán como `OTROS`.
- **FR-007 (Silver - Merge):** El pipeline DEBE consolidar los datos de Seguimiento y Nominal mediante un cruce por la llave sintética compuesta `paciente_id + edad + sexo` condicionado a una ventana temporal máxima de 7 días entre la fecha de notificación y la de ingreso.
- **FR-008 (Calidad - El Guantelete):** Todos los módulos de ingesta (`src/covid_analytics/ingestion/`) y limpieza/cruce (`src/covid_analytics/cleaning/`) DEBEN contar con un tipado estricto completo que pase `mypy --strict src` sin errores ni excepciones.
- **FR-009: Estandarización Canónica de Resultado de Prueba y Estatus del Paciente**

  El motor de limpieza `cleaning/`) debe normalizar semánticamente los valores crudos de `resultado` y `estatus` mediante diccionarios canónicos cerrados:

  1. **Valores Canónicos de `resultado_prueba`:**

     - `POSITIVO`: `['POSITIVO', 'SARS-COV-2', 'DETECTADO', 'POS', 'CONFIRMADO', '+', 'REACTIVO']`

     - `NEGATIVO`: `['NEGATIVO', 'NO DETECTADO', 'NEG', '-', 'NO REACTIVO']`

     - `PENDIENTE`: `['PENDIENTE', 'PEDIENTE', 'EN PROCESO', 'EN ANALISIS', 'S/R', 'SIN RESULTADO', 'TRAMITE', 'NO SE TOMO', 'NO SE TOMÓ']`

     - `NO_CONCLUYENTE`: `['INSUFICIENTE', 'NO CONCLUYENTE', 'INDETERMINADO', 'MUESTRA INADECUADA', 'REPETIR', 'RECHAZO', 'RECHAZADA']`

     - *Fallback:* Valores vacíos o no reconocidos se asignan a `'NO_ESPECIFICADO'`.

  2. **Valores Canónicos de `estatus_paciente`:**

     - `AMBULATORIO`: `['AMBULATORIO', 'DOMICILIO', 'CASA', 'ALTA', 'ESTABLE']`

     - `HOSPITALIZADO`: `['HOSPITALIZADO', 'HOSPITAL', 'INTERNADO', 'UCI', 'TERAPIA INTENSIVA', 'URGENCIAS']`

     - `DEFUNCION`: `['DEFUNCION', 'FINADO', 'FALLECIDO', 'MUERTE', 'OBITO', 'DECEDIDO']`

     - *Fallback:* Valores vacíos o no reconocidos se asignan a `'NO_ESPECIFICADO'`.

### Key Entities

- **CasoBronze:** Estructura de datos temporal en memoria posterior a la ingesta cruda. Posee el campo `paciente_id` ya hasheado y conserva los campos clínicos originales sin normalizar.
- **CasoUnificadoSilver:** Entidad completamente limpia y tipada lista para análisis, estructurada bajo el contrato Pydantic `CasoUnificadoSilver` y persistida en formato Parquet.
- **ResumenCalidad:** Registro de telemetría y auditoría del procesamiento con métricas de completitud, conteo de filas y tasas de merge, guardado en `data_quality_summary.json`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Privacidad):** 100% de los campos PII originales de texto plano son eliminados o hasheados. Cero trazas de nombres reales, teléfonos o direcciones se escriben en disco o logs durante la ejecución del pipeline.
- **SC-002 (Memoria):** El consumo pico de memoria RAM del proceso de ingesta no supera los 500 MB al cargar y procesar las hojas completas del Excel fuente.
- **SC-003 (Métricas de Calidad):** El pipeline genera con éxito el archivo `data_quality_summary.json` detallando el 100% de las llaves especificadas en la sección de Persistencia.
- **SC-004 (El Guantelete):** Los módulos implementados aprueban con éxito los siguientes gates automatizados de calidad de código:
  - `mypy --strict src` en estado verde (cero advertencias/errores).
  - `ruff check src tests` sin infracciones.
  - `pytest --cov=src --cov-fail-under=90` pasando con éxito todas las pruebas unitarias usando fixtures sintéticos con una cobertura igual o superior al 90%.

---

## Assumptions

- **Configuración de la Sal (Salt):** Se asume que la variable de entorno `COVID_PII_SALT` está configurada de forma consistente en el entorno de ejecución para asegurar la consistencia del hash de seudonimización entre corridas temporales diferentes. En su ausencia, el pipeline utilizará un fallback determinista hardcodeado bien documentado en el código.
- **Presencia de Columnas Consecutivas:** Se asume que la columna `NO. (consecutivo)` en Seguimiento y `NO.` en Nominal son únicas y actúan adecuadamente como identificador de registro o `Folio` para construir el hash compuesto.
- **Librerías Disponibles:** Se asume el uso de `pandas`, `openpyxl` (para parsing seguro de Excel en modo de solo lectura) y `pyarrow`/`fastparquet` (para la escritura optimizada del Parquet Silver) dentro del entorno virtual configurado.

