# Contrato de Datos: `data/gold/distribucion_geografica.parquet`

Consumidores de mapas coropléticos y análisis territorial (GIS) DEBEN depender de este contrato.

- **Formato**: Apache Parquet, compresión `snappy`, engine `pyarrow`.
- **Nivel de agregación**: Municipio de residencia (`municipio_residencia`).
- **Garantía de privacidad**: Cero PII. Agregación estadística territorial.

## Esquema de Columnas

| Columna | Tipo lógico | Nulable | Restricción / Contrato |
|---|---|---|---|
| `municipio_residencia` | `string` | No | Nombre estandarizado según catálogo canónico (`NEZAHUALCOYOTL`, `CHIMALHUACAN`, `OTROS`, etc.) |
| `total_casos` | `int64` | No | Total de registros asociados al municipio (`>= 0`) |
| `total_positivos` | `int64` | No | Casos confirmados positivos (`>= 0`) |
| `total_negativos` | `int64` | No | Casos descartados negativos (`>= 0`) |
| `total_hospitalizados` | `int64` | No | Casos con estatus `HOSPITALIZADO` (`>= 0`) |
| `total_defunciones` | `int64` | No | Casos con estatus `DEFUNCION` (`>= 0`) |
| `tasa_positividad` | `float64` | No | `positivos / (positivos + negativos)`; `0.0` si denominador es 0 |
| `tasa_letalidad` | `float64` | No | `defunciones_positivas / total_positivos`; `0.0` si denominador es 0 |
| `tasa_hospitalizacion` | `float64` | No | `hospitalizados_positivos / total_positivos`; `0.0` si denominador es 0 |

## Reglas de Integridad

1. La sumatoria de `total_casos` a través de todos los municipios DEBE igualar el número de filas del dataset Silver.
2. Los nombres en `municipio_residencia` deben coincidir exactamente con el catálogo de normalización para asegurar compatibilidad con `mapa_mexico/Division_Municipal_Mexico_2010.shp`.
