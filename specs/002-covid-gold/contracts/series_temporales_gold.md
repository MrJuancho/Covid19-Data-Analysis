# Contrato de Datos: `data/gold/series_temporales.parquet`

Consumidores de curvas epidemiológicas y análisis de series de tiempo DEBEN depender de este contrato.

- **Formato**: Apache Parquet, compresión `snappy`, engine `pyarrow`.
- **Frecuencia temporal**: Diaria (índice continuo sin huecos de fecha).
- **Garantía de privacidad**: Cero PII. Agregación estadística anónima.

## Esquema de Columnas

| Columna | Tipo lógico | Nulable | Restricción / Contrato |
|---|---|---|---|
| `fecha` | `date32[day]` o `timestamp[ns]` | No | Fecha calendario continua en formato `YYYY-MM-DD` |
| `casos_notificados` | `int64` | No | Conteos diarios basados en `fecha_notificacion` (`>= 0`) |
| `pruebas_tomadas` | `int64` | No | Conteos diarios basados en `fecha_toma_muestra` (`>= 0`) |
| `resultados_positivos` | `int64` | No | Conteos diarios de pruebas positivas por `fecha_resultado` (`>= 0`) |
| `resultados_negativos` | `int64` | No | Conteos diarios de pruebas negativas por `fecha_resultado` (`>= 0`) |
| `ingresos_hospitalarios` | `int64` | No | Conteos diarios basados en `fecha_ingreso_hospital` (`>= 0`) |
| `defunciones` | `int64` | No | Conteos diarios de estatus `DEFUNCION` (`>= 0`) |
| `media_movil_7d_positivos` | `float64` | No | Media móvil de 7 días retrospectiva de `resultados_positivos` (`>= 0.0`) |
| `casos_positivos_acumulados` | `int64` | No | Suma acumulada progresiva de `resultados_positivos` (`>= 0`) |

## Reglas de Integridad

1. El rango de `fecha` DEBE ser continuo entre $\min(\text{fecha})$ y $\max(\text{fecha})$ detectados en el dataset Silver.
2. Los días sin registros DEBEN registrarse explícitamente con `0` en conteos y el valor correspondiente en la media móvil.
