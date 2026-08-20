# Contrato de Datos: `data/silver/casos_unificados.parquet`

Consumidores externos (futuras capas Gold, notebooks de análisis, dashboards) DEBEN
depender únicamente de este contrato, no de la implementación interna del pipeline.

- **Formato**: Apache Parquet, compresión `snappy`, engine `pyarrow`.
- **Modelo Pydantic de origen**: `CasoUnificadoSilver` (ver `data-model.md`).
- **Garantía de privacidad**: cero columnas PII (nombre, dirección, teléfono) en texto
  plano. Solo existe `paciente_id` (hash SHA-256 irreversible).

## Esquema de columnas

| Columna | Tipo lógico (pandas/pyarrow) | Nulable | Contrato |
|---|---|---|---|
| `paciente_id` | `string` | No | 64 caracteres hex |
| `edad` | `float64` | No (usa `-1.0` como sentinel) | `>= -1.0` |
| `sexo` | `string` (categórico cerrado) | No | uno de `F`, `M`, `OTRO`, `INDETERMINADO` |
| `municipio_residencia` | `string` | No (usa `"OTROS"` como sentinel) | catálogo cerrado + `"OTROS"` |
| `derechohabiencia` | `string` | No (usa `"NINGUNO"` como sentinel) | — |
| `fecha_notificacion` | `datetime64[ns]` | Sí (`NaT` permitido) | — |
| `fecha_toma_muestra` | `datetime64[ns]` | Sí (`NaT` permitido) | — |
| `fecha_resultado` | `datetime64[ns]` | Sí (`NaT` permitido) | — |
| `resultado_prueba` | `string` (categórico cerrado) | No | uno de `POSITIVO`, `NEGATIVO`, `PENDIENTE`, `NO_CONCLUYENTE`, `NO_ESPECIFICADO` (diccionario canónico, FR-009) |
| `estatus_paciente` | `string` (categórico cerrado) | No | uno de `AMBULATORIO`, `HOSPITALIZADO`, `DEFUNCION`, `NO_ESPECIFICADO` (diccionario canónico, FR-009) |
| `hospital` | `string` | Sí | solo presente si hubo cruce con Nominal |
| `fecha_ingreso_hospital` | `datetime64[ns]` | Sí | solo presente si hubo cruce con Nominal |
| `es_registro_unificado` | `bool` | No | — |
| `dias_entre_notificacion_e_ingreso` | `Int64` (nullable) | Sí | `<= 7` cuando `es_registro_unificado = True`; `null` si `False` |

## Garantías de compatibilidad

- Este contrato solo puede recibir cambios **aditivos** (nuevas columnas opcionales) sin
  bump MAJOR de la Constitución del proyecto — remover o retipar una columna existente
  cuenta como cambio incompatible y requiere actualizar `spec.md` primero (Principio IV,
  SDD Estricto).
- Cualquier consumidor externo DEBE tolerar columnas adicionales no documentadas aquí
  (forward-compatible read).
