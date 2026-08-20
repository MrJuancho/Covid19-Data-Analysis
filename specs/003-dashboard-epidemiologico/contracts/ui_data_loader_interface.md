# Contrato de Interfaz: `src/covid_analytics/ui/data_loader.py`

Módulo interno consumido exclusivamente por `ui/app.py`. No es una API pública ni un CLI —
documentado aquí porque fija el contrato de resiliencia (FR-013) y privacidad (FR-002) que
`app.py` y sus tests asumen.

## Funciones expuestas

| Función | Firma | Contrato |
|---|---|---|
| `cargar_metricas_demografia` | `(ruta: Path = Path("data/gold/metricas_demografia.parquet")) -> pd.DataFrame \| None` | `None` si el archivo no existe. Nunca lanza excepción por archivo ausente. Cacheada con `@st.cache_data`, clave invalidada por `(ruta, mtime)`. |
| `cargar_series_temporales` | `(ruta: Path = Path("data/gold/series_temporales.parquet")) -> pd.DataFrame \| None` | Igual contrato que arriba. |
| `cargar_distribucion_geografica` | `(ruta: Path = Path("data/gold/distribucion_geografica.parquet")) -> pd.DataFrame \| None` | Igual contrato que arriba. |
| `cargar_kpis_generales` | `(ruta: Path = Path("data/gold/kpis_generales.parquet")) -> pd.DataFrame \| None` | Igual contrato que arriba. |
| `cargar_metricas_derechohabiencia` | `(ruta: Path = Path("data/gold/metricas_derechohabiencia.parquet")) -> pd.DataFrame \| None` | Igual contrato que arriba. |
| `cargar_reporte_calidad` | `(ruta: Path = Path("data/silver/data_quality_summary.json")) -> dict[str, object] \| None` | `None` si el archivo no existe o el JSON es inválido (nunca propaga `JSONDecodeError`). Única función que lee fuera de `data/gold/` (FR-002, whitelist explícita). |
| `cargar_geojson_municipios` | `(ruta: Path = Path("mapa_mexico/Division_Municipal_Mexico_2010.shp")) -> dict[str, object] \| None` | `None` si el shapefile no existe. Cacheada con `@st.cache_resource` (recurso inmutable, no serializable por valor como un DataFrame). |

## Garantías

1. **Cero PII**: ninguna función de este módulo lee `data/bronze/*` ni ninguna columna que
   contenga `paciente_id` u otro identificador individual. `cargar_reporte_calidad` solo expone
   los campos agregados de `ResumenCalidad` (001-covid-etl), ya validados sin PII.
2. **Resiliencia**: ninguna función lanza excepción por archivo ausente o corrupto — siempre
   retorna `None` en ese caso, dejando que `app.py` decida el estado de UI (FR-013).
3. **Frescura**: si el archivo en `ruta` cambia en disco (ej. por una re-ejecución del pipeline
   Gold), la próxima llamada dentro de la misma sesión de Streamlit DEBE reflejar el contenido
   nuevo, no una copia obsoleta de caché (ver `research.md` §6).
4. **Sin transformación**: estas funciones solo leen y devuelven el `DataFrame`/`dict` tal cual
   persiste en disco — ninguna agregación, filtrado o reindexado ocurre aquí (eso vive en
   `ui/filtros.py`, ver `contracts/ui_filtros_interface.md`).
