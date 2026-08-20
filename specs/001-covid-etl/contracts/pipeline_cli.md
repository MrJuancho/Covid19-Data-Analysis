# Contrato de Interfaz: CLI del pipeline

El pipeline se expone como un entrypoint ejecutable de línea de comandos —
no hay API HTTP ni librería pública de terceros en el alcance de esta feature.

## Invocación

```bash
uv run python -m covid_analytics.pipeline \
  --excel-path "RED-NEGATIVA-COVID-02_VIGILANCIA-HOSPITALARIA 11.01.21.xlsx" \
  --output-dir data/silver
```

## Variables de entorno

| Variable | Requerida | Efecto |
|---|---|---|
| `COVID_PII_SALT` | No (recomendada) | Sal usada en `SHA256(Nombre_Normalizado + Folio + Sal)`. Si está ausente, se usa un fallback determinista documentado en código y se emite un warning (research.md §6). |

## Argumentos

| Argumento | Tipo | Default | Descripción |
|---|---|---|---|
| `--excel-path` | `str` (ruta) | — (obligatorio) | ruta al `.xlsx` de origen con las 3 hojas auditadas |
| `--output-dir` | `str` (ruta) | `data/silver` | carpeta destino de `casos_unificados.parquet` y `data_quality_summary.json` |

## Salidas

- **Código de salida `0`**: pipeline completado; se escribieron
  `casos_unificados.parquet` (contrato: `contracts/casos_unificados_silver.md`) y
  `data_quality_summary.json` (contrato: `contracts/data_quality_summary.md`) en
  `--output-dir`.
- **Código de salida `!= 0`**: error irrecuperable (p. ej. archivo Excel no encontrado o
  hoja esperada ausente). El mensaje de error DEBE ir a `stderr` y NUNCA DEBE incluir
  valores de columnas PII, solo nombres de columna/hoja y conteos.

## Logging

- Salida estructurada a `stdout`/logs de nivel `INFO` con conteos agregados por fase
  (Bronze/Silver/merge); nivel `WARNING` para fallback de sal o correcciones de columnas
  intercambiadas. Ningún log, en ningún nivel, imprime valores de columnas PII
  (Principio I de la Constitución — ver también `contracts/data_quality_summary.md`).
