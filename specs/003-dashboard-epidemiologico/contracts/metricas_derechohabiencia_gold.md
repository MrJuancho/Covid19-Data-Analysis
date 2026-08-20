# Contrato de Datos: `data/gold/metricas_derechohabiencia.parquet`

Consumidores del tablero (`src/covid_analytics/ui/`) DEBEN depender de este contrato para la
Pestaña 4 (Riesgo Clínico) y el filtro de derechohabiencia. Extiende la capa Gold de
002-covid-gold (FR-006a de `specs/003-dashboard-epidemiologico/spec.md`).

- **Formato**: Apache Parquet, compresión `snappy`, engine `pyarrow`.
- **Nivel de agregación**: Combinación única de `(derechohabiencia, resultado_prueba, estatus_paciente)`.
- **Garantía de privacidad**: Cero PII. Agregación estadística anónima.

## Esquema de Columnas

| Columna | Tipo lógico | Nulable | Restricción / Contrato |
|---|---|---|---|
| `derechohabiencia` | `string` | No | Uno de `IMSS`, `ISSSTE`, `ISSEMYM`, `INSABI`, `PRIVADO`, `NINGUNA`, `OTRA` |
| `resultado_prueba` | `string` | No | Uno de `POSITIVO`, `NEGATIVO`, `PENDIENTE`, `NO_CONCLUYENTE`, `NO_ESPECIFICADO` |
| `estatus_paciente` | `string` | No | Uno de `AMBULATORIO`, `HOSPITALIZADO`, `DEFUNCION`, `NO_ESPECIFICADO` |
| `total_casos` | `int64` | No | `>= 0` |
| `porcentaje_del_total` | `float64` | No | `0.0 <= x <= 1.0` |
| `tasa_positividad_grupo` | `float64` | No | `0.0 <= x <= 1.0` |
| `tasa_hospitalizacion_grupo` | `float64` | No | `0.0 <= x <= 1.0` |
| `tasa_letalidad_grupo` | `float64` | No | `0.0 <= x <= 1.0` |

## Reglas de Estandarización del Catálogo

`derechohabiencia` es texto libre en `casos_unificados.parquet` (Silver). Esta tabla DEBE
normalizarlo así:

| Valor Silver observado (ejemplos) | Valor Gold estandarizado |
|---|---|
| `IMSS` (case-insensitive, con/sin espacios) | `IMSS` |
| `ISSSTE` | `ISSSTE` |
| `ISSEMYM` | `ISSEMYM` |
| `INSABI` | `INSABI` |
| `PRIVADO`, `PRIVADA` | `PRIVADO` |
| `NINGUNO`, `NINGUNA`, vacío/nulo (sentinel Silver) | `NINGUNA` |
| Cualquier otro valor (ej. `SEDENA`, variantes de captura no reconocidas) | `OTRA` |

## Reglas de Integridad

1. La sumatoria de `total_casos` sobre todas las filas DEBE ser idéntica al número de filas de
   `data/silver/casos_unificados.parquet` (mismo principio que FR-007 de 002-covid-gold).
2. La sumatoria de `total_casos` donde `resultado_prueba = "POSITIVO"` DEBE coincidir
   exactamente con el total de positivos reportado por `kpis_generales.parquet` y
   `metricas_demografia.parquet` (extiende `verificar_consistencia_marginal`,
   `src/covid_analytics/analytics/engine.py`).
3. Si una combinación no tiene casos observados, puede omitirse o tener `total_casos = 0` con las
   tasas en `0.0`.
