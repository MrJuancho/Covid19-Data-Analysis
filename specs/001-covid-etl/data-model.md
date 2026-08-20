# Data Model: Pipeline ETL de COVID-19 (Bronze a Silver)

Deriva las entidades de `spec.md#Key Entities` y de los layouts reales documentados en
`docs/audit_legacy.md`. Todos los campos marcados **PII** deben desaparecer al salir de la
capa Bronze (Constitución, Principio I).

## CasoBronze

Estructura intermedia en memoria, inmediatamente posterior a la ingesta cruda + hash de
PII. Nunca se persiste a disco.

| Campo | Tipo | Origen (hoja) | Notas |
|---|---|---|---|
| `paciente_id` | `str` (hex SHA-256, 64 chars) | derivado | `SHA256(Normalizar(Nombre) + str(Folio) + Sal)` — ver FR-002 |
| `fuente` | `Literal["seguimiento", "nominal"]` | derivado | identifica la hoja de origen del registro |
| `folio_origen` | `str \| None` | `NO. (consecutivo)` / `NO.` | usado solo para construir el hash; no se re-expone tal cual fuera del hash |
| `sexo_raw` | `str \| None` | `SEXO (M/F)` / — | valor sin normalizar, listo para limpieza Silver |
| `edad_raw` | `str \| None` | `EDAD` / `EDAD \| F` / `EDAD \| M` | valor sin normalizar (puede ser `"RN"`, `"3M"`, numérico como string, etc.) |
| `municipio_raw` | `str \| None` | `MUNICIPIO/PAÍS RESIDENCIA` | solo en Seguimiento |
| `derechohabiencia_raw` | `str \| None` | `DERECHOHABIENCIA` | solo en Seguimiento |
| `fecha_notificacion_raw` | `datetime \| int \| str \| None` | `FECHA DE NOTIFICACIÓN` | sin parsear aún |
| `fecha_toma_muestra_raw` | `datetime \| int \| str \| None` | `FECHA TOMA DE MUESTRA` / `TOMA DE MUESTRA FECHA` | sin parsear |
| `resultado_raw` | `str \| None` | `RESULTADO` | puede contener una fecha mal capturada (ver Edge Cases en spec.md) |
| `fecha_resultado_raw` | `datetime \| int \| str \| None` | `FECHA DE RESULTADO` | sin parsear; puede venir intercambiada con `resultado_raw` |
| `estatus_raw` | `str \| None` | `ESTATUS` | solo en Seguimiento |
| `fecha_ingreso_raw` | `datetime \| int \| str \| None` | `FECHA DE INGRESO O DE ATENCIÓN` | solo en Nominal |
| `hospital_raw` | `str \| None` | `HOSPITAL` | solo en Nominal |

**PII eliminados inmediatamente tras el hash** (nunca llegan a `CasoBronze`): `CASO`,
`NOMBRE DEL PACIENTE`, `CALLE`, `NO. EXT.`, `NO. INT.`, `COLONIA`, `LOCALIDAD`,
`TELÉFONO`.

**Reglas de validación**:
- `paciente_id` DEBE tener longitud exacta 64 (hex de SHA-256).
- `fuente` es obligatorio y cerrado a los dos valores del `Literal`.

## CasoUnificadoSilver

Entidad limpia, tipada y unificada, contrato Pydantic persistido en
`data/silver/casos_unificados.parquet`.

| Campo | Tipo | Regla de validación / derivación |
|---|---|---|
| `paciente_id` | `str` | hereda de `CasoBronze`; clave de unión heurística (FR-007) |
| `edad` | `float64` | consolidado de `EDAD \| F` / `EDAD \| M` (FR-004); `-1.0` si ambos son nulos (Edge Case) |
| `sexo` | `Literal["F", "M", "OTRO", "INDETERMINADO"]` | normalizado; `INDETERMINADO` si no se puede inferir (Edge Case) |
| `municipio_residencia` | `str` | mapeado por catálogo explícito (FR-006); `"OTROS"` si no coincide con el catálogo |
| `derechohabiencia` | `str` | `"NINGUNO"` si nulo |
| `fecha_notificacion` | `datetime \| NaT` | vía `parse_fecha_polimorfica` (research.md §3) |
| `fecha_toma_muestra` | `datetime \| NaT` | ídem |
| `fecha_resultado` | `datetime \| NaT` | ídem; corregida si venía intercambiada con `resultado_prueba` (FR de Silver - corrector de columnas) |
| `resultado_prueba` | `Literal["POSITIVO", "NEGATIVO", "PENDIENTE", "NO_CONCLUYENTE", "NO_ESPECIFICADO"]` | normalizado vía diccionario canónico cerrado (FR-009) |
| `estatus_paciente` | `Literal["AMBULATORIO", "HOSPITALIZADO", "DEFUNCION", "NO_ESPECIFICADO"]` | normalizado vía diccionario canónico cerrado (FR-009); `ALTA`/`ESTABLE` se mapean a `AMBULATORIO` |
| `hospital` | `str \| None` | solo presente si el registro tiene origen/cruce con Nominal |
| `fecha_ingreso_hospital` | `datetime \| NaT \| None` | solo si hubo cruce con Nominal (User Story 3) |
| `es_registro_unificado` | `bool` | `True` si el registro proviene de un merge Seguimiento+Nominal exitoso; `False` si es huérfano de una sola fuente |
| `dias_entre_notificacion_e_ingreso` | `int \| None` | `None` si `es_registro_unificado` es `False` |

**Reglas de validación**:
- `edad` DEBE ser `>= -1.0` (permite el sentinel `-1.0` documentado, prohíbe negativos
  arbitrarios).
- Si `es_registro_unificado` es `True`, `dias_entre_notificacion_e_ingreso` DEBE ser
  `<= 7` (regla de cruce, FR-007 / User Story 3, Acceptance Scenario 1).
- Ninguno de los campos PII originales (`CASO`, `NOMBRE DEL PACIENTE`, direcciones,
  teléfono) existe en este modelo — es una invariante estructural, no solo de valor.

## ResumenCalidad

Registro de telemetría, persistido en `data_quality_summary.json` al final de cada
corrida (User Story 4).

| Campo | Tipo | Descripción |
|---|---|---|
| `filas_leidas_bronze_seguimiento` | `int` | filas crudas leídas de `SEGUIMIENTO DE CASOS COVID 19` |
| `filas_leidas_bronze_nominal` | `int` | filas crudas leídas de ` NOMINAL DE HOSPITALIZADOS` |
| `registros_hasheados` | `int` | total de `paciente_id` generados |
| `cruces_exitosos` | `int` | registros con `es_registro_unificado = True` |
| `registros_huerfanos` | `int` | registros con `es_registro_unificado = False` |
| `porcentaje_huerfanos` | `float` | `registros_huerfanos / (cruces_exitosos + registros_huerfanos)` |
| `correcciones_columnas_intercambiadas` | `int` | veces que se aplicó el corrector Resultado↔Fecha Resultado |
| `colisiones_llave_sintetica` | `int` | casos de homónimos con múltiples admisiones (Edge Case) resueltos por `|Δt|` mínimo |
| `timestamp_ejecucion` | `datetime` (ISO 8601) | momento en que terminó el pipeline |

**Reglas de validación**: todos los campos numéricos DEBEN ser `>= 0` (SC-003: "ninguna
métrica en nulo").

## Relaciones

```text
CasoBronze (fuente="seguimiento")  ─┐
                                     ├─ merge heurístico (paciente_id + edad + sexo,
CasoBronze (fuente="nominal")     ──┘   ventana ≤7 días)  ──►  CasoUnificadoSilver

[CasoUnificadoSilver] (todos los registros de una corrida)  ──►  ResumenCalidad (1 por corrida)
```
