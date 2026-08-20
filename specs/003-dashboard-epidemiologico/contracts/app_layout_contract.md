# Contrato de Interfaz: Layout de `src/covid_analytics/ui/app.py`

Fija los `key` de widgets, el orden de pestañas y las etiquetas de las tarjetas KPI que
`tests/unit/test_ui_app.py` (`streamlit.testing.v1.AppTest`) usa para localizar elementos. Un
cambio en esta tabla es un cambio de contrato y DEBE reflejarse aquí antes de tocar `app.py`.

## Sidebar — Filtros (FR-003..FR-006)

| Widget | Tipo Streamlit | `key` | Notas |
|---|---|---|---|
| Rango de fechas | `st.slider` (tupla de `date`) | `"filtro_fechas"` | Límites = `[min(fecha), max(fecha)]` de `series_temporales.parquet`, acotado a `[2020-01-01, 2023-12-31]` |
| Sexo | `st.multiselect` | `"filtro_sexo"` | Opciones: `["MASCULINO", "FEMENINO"]` (etiquetas de UI, mapeadas a `M`/`F`) |
| Grupo etario | `st.multiselect` | `"filtro_grupo_edad"` | Opciones: `["<18", "18-39", "40-59", "60+"]` |
| Derechohabiencia | `st.multiselect` | `"filtro_derechohabiencia"` | Opciones: `["IMSS", "ISSSTE", "ISSEMYM", "INSABI", "PRIVADO", "NINGUNA"]` |

## Tarjetas KPI (FR-007)

| Orden | `st.metric(label=...)` | Fuente (`VistaKPI`) |
|---|---|---|
| 1 | `"Total Pruebas"` | `total_pruebas` |
| 2 | `"Casos Positivos Confirmados"` | `casos_positivos_confirmados` |
| 3 | `"Tasa Global de Positividad"` | `tasa_global_positividad` (formateado `%`) |
| 4 | `"Tasa de Hospitalización"` | `tasa_hospitalizacion` (formateado `%`) |

## Pestañas (`st.tabs`, orden fijo)

| Índice | Título de pestaña | Requisito | Archivo Gold requerido |
|---|---|---|---|
| 0 | `"Curva Epidemiológica"` | FR-008 | `series_temporales.parquet` |
| 1 | `"Demografía & Pirámide"` | FR-009 | `metricas_demografia.parquet` |
| 2 | `"Distribución Geoespacial"` | FR-010 | `distribucion_geografica.parquet` + `mapa_mexico/*.shp` |
| 3 | `"Riesgo Clínico"` | FR-011 | `metricas_derechohabiencia.parquet` |
| 4 | `"Calidad & Telemetría"` | FR-012 | `data/silver/data_quality_summary.json` |

## Estados vacíos (FR-013)

| Escenario | Elemento mostrado |
|---|---|
| Ningún archivo Gold existe | `st.info` a nivel de página completa, antes de renderizar sidebar/tabs: *"Ejecute el pipeline Gold antes de usar el tablero."* |
| Un archivo Gold individual falta | `st.info` dentro de la pestaña/tarjeta afectada únicamente: *"[Nombre de vista] no disponible: falta `<archivo>`."* — el resto del tablero funciona con normalidad |
| Combinación de filtros sin resultados | `st.info` dentro de la visualización afectada: *"Sin datos para esta selección."* |
| `data_quality_summary.json` ausente | `st.info` solo dentro de la Pestaña 5: *"Reporte de calidad no disponible."* |

## Garantías para `AppTest`

1. Todo widget interactivo (sliders, multiselects) DEBE declarar `key` explícito según la tabla
   de arriba — `AppTest` localiza y muta valores por `key`, no por posición ni por texto de label.
2. Las etiquetas de `st.metric` y los títulos de `st.tabs` son literales exactos de este contrato
   — cambiarlos requiere actualizar esta tabla y los tests en el mismo commit.
3. `app.py` nunca debe lanzar una excepción no controlada durante `AppTest.run()` para ninguna
   combinación de archivos Gold presentes/ausentes cubierta por FR-013.
