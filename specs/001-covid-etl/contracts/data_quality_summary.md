# Contrato de Datos: `data_quality_summary.json`

Reporte de telemetría de una corrida del pipeline, generado siempre al final de una
ejecución exitosa (User Story 4). Formato: JSON, UTF-8, objeto plano (sin anidamiento).

## Esquema

```json
{
  "filas_leidas_bronze_seguimiento": 5986,
  "filas_leidas_bronze_nominal": 5992,
  "registros_hasheados": 11978,
  "cruces_exitosos": 0,
  "registros_huerfanos": 0,
  "porcentaje_huerfanos": 0.0,
  "correcciones_columnas_intercambiadas": 0,
  "colisiones_llave_sintetica": 0,
  "fechas_anomalas_fuera_ventana": 0,
  "timestamp_ejecucion": "2026-08-19T00:00:00Z"
}
```

| Campo | Tipo JSON | Contrato |
|---|---|---|
| `filas_leidas_bronze_seguimiento` | number (entero) | `>= 0` |
| `filas_leidas_bronze_nominal` | number (entero) | `>= 0` |
| `registros_hasheados` | number (entero) | `>= 0` |
| `cruces_exitosos` | number (entero) | `>= 0` |
| `registros_huerfanos` | number (entero) | `>= 0` |
| `porcentaje_huerfanos` | number (float, 0.0–1.0) | `registros_huerfanos / (cruces_exitosos + registros_huerfanos)`; `0.0` si el denominador es `0` |
| `correcciones_columnas_intercambiadas` | number (entero) | `>= 0` |
| `colisiones_llave_sintetica` | number (entero) | `>= 0` |
| `fechas_anomalas_fuera_ventana` | number (entero) | `>= 0`; fechas que parsearon estructuralmente pero cayeron fuera de `[FECHA_MIN_VALIDA, FECHA_MAX_VALIDA]` (típicamente typos de año, ej. `"0202"` o `"2920"` en vez de `"2020"`) y por lo tanto se descartaron como `NaT` (campo aditivo) |
| `timestamp_ejecucion` | string (ISO 8601, UTC) | momento de finalización del pipeline |

## Garantías

- Ninguna clave puede ser `null` (SC-003: "ninguna métrica en nulo"); un valor ausente se
  reporta como `0` o `0.0`, nunca se omite la clave.
- No contiene, bajo ninguna circunstancia, PII (nombres, folios individuales, hashes de
  paciente) — es un resumen agregado únicamente.
