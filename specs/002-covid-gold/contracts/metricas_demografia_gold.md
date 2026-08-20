# Contrato de Datos: `data/gold/metricas_demografia.parquet`

Consumidores de visualización y dashboards DEBEN depender de este contrato para análisis demográficos.

- **Formato**: Apache Parquet, compresión `snappy`, engine `pyarrow`.
- **Nivel de agregación**: Combinación única de `(grupo_edad, sexo, resultado_prueba, estatus_paciente)`.
- **Garantía de privacidad**: Cero PII. Agregación estadística anónima.

## Esquema de Columnas

| Columna | Tipo lógico | Nulable | Restricción / Contrato |
|---|---|---|---|
| `grupo_edad` | `string` | No | Uno de los 14 grupos canónicos (`0-1`, `2-11`, ..., `66+`, `SIN_DATO`) |
| `sexo` | `string` | No | Uno de `F`, `M`, `OTRO`, `INDETERMINADO` |
| `resultado_prueba` | `string` | No | Uno de `POSITIVO`, `NEGATIVO`, `PENDIENTE`, `NO_CONCLUYENTE`, `NO_ESPECIFICADO` |
| `estatus_paciente` | `string` | No | Uno de `AMBULATORIO`, `HOSPITALIZADO`, `DEFUNCION`, `NO_ESPECIFICADO` |
| `total_casos` | `int64` | No | `>= 0` |
| `porcentaje_del_total` | `float64` | No | `0.0 <= x <= 1.0` (porcentaje sobre el total global de casos) |
| `tasa_positividad_grupo` | `float64` | No | `0.0 <= x <= 1.0` (positivos en el grupo / evaluados en el grupo) |

## Reglas de Integridad

1. La sumatoria de `total_casos` sobre todas las filas DEBE ser idéntica al conteo de filas de `data/silver/casos_unificados.parquet`.
2. Si una combinación de categorías no tiene casos observados, puede omitirse o tener `total_casos = 0` y `porcentaje_del_total = 0.0`.
