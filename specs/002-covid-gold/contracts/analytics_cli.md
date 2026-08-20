# Contrato de Interfaz CLI: Módulo Analítico Gold

Define la interfaz de línea de comandos para la ejecución de las transformaciones de la capa Gold (`src/covid_analytics/analytics/`).

## Invocación

```bash
uv run python -m covid_analytics.pipeline --layer gold
# o invocación directa del módulo analítico
uv run python -m covid_analytics.analytics.engine --silver-path data/silver/casos_unificados.parquet --output-dir data/gold
```

## Argumentos

| Argumento | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `--silver-path` | `Path` (string) | `data/silver/casos_unificados.parquet` | Ruta al dataset Parquet limpio de la capa Silver |
| `--output-dir` | `Path` (string) | `data/gold` | Directorio destino para persistir las tablas Parquet y resúmenes JSON |
| `--verbose` | `flag` | `False` | Activa logs de depuración (garantizando cero PII en stdout) |

## Códigos de Salida

- `0`: Ejecución exitosa. Todas las tablas Gold y resúmenes exportados.
- `1`: Error de lectura de capa Silver (archivo inexistente o corrupto).
- `2`: Violación de contrato de datos o error de integridad estadística.
