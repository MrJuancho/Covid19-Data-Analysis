# Contrato de Datos: `data/gold/kpis_generales.parquet` y `data/gold/resumen_ejecutivo.json`

Consumidores ejecutivos y tableros de control de alto nivel DEBEN depender de este contrato.

- **Formato**: Apache Parquet (`kpis_generales.parquet`) y JSON UTF-8 plano (`resumen_ejecutivo.json`).
- **Nivel de agregación**: Macro / Global (1 fila).
- **Garantía de privacidad**: Cero PII. Solo indicadores consolidados.

## Esquema de Campos

| Campo | Tipo | Nulable | Restricción / Contrato |
|---|---|---|---|
| `total_pacientes_atendidos` | `int64` | No | Total de registros evaluados (`>= 0`) |
| `total_positivos` | `int64` | No | Total de casos confirmados SARS-CoV-2 (`>= 0`) |
| `total_negativos` | `int64` | No | Total de casos descartados (`>= 0`) |
| `total_pendientes` | `int64` | No | Pruebas en proceso o sin resultado (`>= 0`) |
| `total_no_concluyentes` | `int64` | No | Pruebas inválidas o indeterminadas (`>= 0`) |
| `total_hospitalizados` | `int64` | No | Total de admisiones hospitalarias (`>= 0`) |
| `total_defunciones` | `int64` | No | Total de fallecimientos registrados (`>= 0`) |
| `tasa_global_positividad` | `float64` | No | `positivos / (positivos + negativos)` (`0.0 <= x <= 1.0`) |
| `tasa_global_letalidad` | `float64` | No | `defunciones / positivos` (`0.0 <= x <= 1.0`) |
| `tasa_global_hospitalizacion` | `float64` | No | `hospitalizados / positivos` (`0.0 <= x <= 1.0`) |
| `registros_unificados_cruce` | `int64` | No | Casos con trazabilidad completa ambulatorio-hospitalario (`>= 0`) |
| `mediana_dias_notificacion_ingreso` | `float64` | Sí | Mediana del desfase temporal de internamiento; `null` si no hay cruces |
| `casos_fechas_invertidas` | `int64` | No | Conteo de casos con `fecha_resultado < fecha_toma_muestra` detectados por la serie temporal (`>= 0`, FR-004a). Campo aditivo — no forma parte de la agregación por filas, es telemetría global |
| `timestamp_generacion` | `string` | No | Formato ISO 8601 UTC |

## Garantías

1. Los campos no pueden ser `null` a excepción de `mediana_dias_notificacion_ingreso` en datasets sin cruces.
2. La suma `total_positivos + total_negativos + total_pendientes + total_no_concluyentes + otros` DEBE coincidir con `total_pacientes_atendidos`.
