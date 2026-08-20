# Research: Dashboard Epidemiológico Interactivo (Streamlit)

**Feature**: `003-dashboard-epidemiologico` | **Spec**: [specs/003-dashboard-epidemiologico/spec.md](./spec.md)

El Technical Context de `plan.md` no contiene marcadores `NEEDS CLARIFICATION`: las 3 ambigüedades
de mayor impacto ya se resolvieron en `/speckit-clarify` (ver `## Clarifications` en `spec.md`).
Este documento registra las decisiones técnicas de implementación restantes.

---

## 1. Framework de UI y estrategia de pruebas

- **Decision**: `streamlit` como framework de UI, probado con `streamlit.testing.v1.AppTest`
  (incluido en el propio paquete `streamlit`, sin dependencia adicional).
- **Rationale**: Mandado explícitamente por la feature; `AppTest` permite ejecutar la app en un
  entorno de test simulado (sin servidor real) y hacer assertions sobre widgets/valores
  renderizados, exactamente lo que pide FR-014.
- **Alternatives considered**: Dash/Panel — descartados porque la feature especifica Streamlit
  explícitamente y el proyecto no tiene infraestructura previa para otro framework web.

## 2. Librería de gráficos (curva, pirámide, barras, mapa)

- **Decision**: `plotly` (vía `plotly.express` para curva/barras/pirámide y
  `plotly.express.choropleth_map`/`choropleth_mapbox` para el mapa geoespacial) como única
  librería de visualización en toda la app.
- **Rationale**: La descripción de la feature deja el mapa abierto entre "Plotly Mapbox / Pydeck
  / Folium", pero ya mandata Plotly Express para las otras 3 pestañas. Usar Plotly también para
  el mapa evita añadir una segunda librería de visualización (menos superficie de dependencias,
  un solo patrón de theming/testing). `choropleth_map`/`choropleth_mapbox` con estilos abiertos
  (`carto-positron`, `open-street-map`) no requiere token de Mapbox, evitando gestión de
  credenciales para una herramienta interna de un solo hospital.
- **Alternatives considered**:
  - `pydeck` (vía `st.pydeck_chart`, incluido en Streamlit sin dependencia extra) — viable y sin
    dependencias nuevas, pero introduce una segunda API de gráficos (capas de pydeck vs. figuras
    Plotly) solo para una pestaña, aumentando la carga cognitiva de mantenimiento sin beneficio
    claro sobre `choropleth_map`.
  - `folium` (vía `streamlit-folium`) — requiere una dependencia adicional puente
    (`streamlit-folium`) solo para embeber Folium en Streamlit; descartado por la misma razón de
    minimizar superficie de dependencias.

## 3. Lectura del shapefile municipal sin GDAL/geopandas

- **Decision**: `pyshp` (`shapefile.Reader`) para leer `mapa_mexico/Division_Municipal_Mexico_2010.shp`
  y convertirlo a un `dict` GeoJSON (`Reader.__geo_interface__`) una sola vez, cacheado con
  `@st.cache_resource` (no `@st.cache_data`, porque un GeoJSON de geometrías es un recurso
  inmutable pesado, no un DataFrame serializable por valor — ver decisión 5).
- **Rationale**: `geopandas` requiere GDAL/Fiona/PyProj, notoriamente frágiles de instalar en
  Windows sin `conda`; el proyecto ya usa `uv` puro. `pyshp` es una librería pura-Python sin
  dependencias binarias, suficiente para una conversión de lectura única a GeoJSON que Plotly
  consume directamente.
- **Alternatives considered**: `geopandas` — descartado por el riesgo de instalación en Windows
  (constraint del entorno de desarrollo, ver `docs/audit_legacy.md` y la ausencia total de
  GDAL/Fiona en `pyproject.toml`).

## 4. Extensión de Gold: columna `grupo_edad_ui` (FR-005a)

- **Decision**: En `analytics/demografia.py`, añadir `asignar_grupo_edad_ui(edad: pd.Series) ->
  pd.Categorical[str]` usando `pd.cut` con cortes exactos `[0.0, 18.0, 40.0, 60.0, inf)` y
  `include_lowest=True`, análogo a `asignar_grupo_edad` (14 bins) ya existente — **no** derivada
  de `grupo_edad`, evitando el error de clasificación en los bins `36-40`/`56-60` identificado en
  `/speckit-clarify`. `calcular_metricas_demografia` se extiende para incluir ambas columnas
  (`grupo_edad`, `grupo_edad_ui`) en el mismo cubo, agregando también por `grupo_edad_ui` sin
  romper la consistencia marginal ya validada por `verificar_consistencia_marginal` (002-covid-gold).
- **Rationale**: Reutiliza el patrón de binning ya probado (`pd.cut` + sentinel `SIN_DATO` para
  edad `< 0` o nula) en vez de introducir una segunda técnica de clasificación.
- **Alternatives considered**: Ninguna — la decisión de fondo (columna exacta vs. aproximación)
  ya se resolvió en `/speckit-clarify`; esta sección solo fija el "cómo" de implementación.

## 5. Extensión de Gold: tabla `metricas_derechohabiencia.parquet` (FR-006a)

- **Decision**: Nuevo módulo `analytics/derechohabiencia.py` con
  `estandarizar_derechohabiencia(valor: str) -> str` (mapea a
  `IMSS`/`ISSSTE`/`ISSEMYM`/`INSABI`/`PRIVADO`/`NINGUNA`/`OTRA`, análogo a
  `estandarizar_municipio` en `cleaning/catalogos.py`) y
  `calcular_metricas_derechohabiencia(df_silver) -> pd.DataFrame`, agregando por
  `(derechohabiencia, resultado_prueba, estatus_paciente)` con las mismas fórmulas de
  `tasa_segura` que `demografia.py`/`geografia.py`. `engine.generar_capa_gold` se extiende para
  invocar esta función, persistir `metricas_derechohabiencia.parquet` y sumar su verificación de
  consistencia marginal (positivos) a `verificar_consistencia_marginal`.
- **Rationale**: Mantiene el patrón establecido en 002-covid-gold (un módulo por dimensión, cubo
  con conteos + tasas, reutilización de `_shared.tasa_segura`); la estandarización del catálogo
  de `derechohabiencia` (texto libre en Silver) sigue el mismo patrón que `municipio_residencia`
  → `"OTROS"` ya validado en 001/002.
- **Alternatives considered**: Calcular la estandarización dentro de `cleaning/` (capa Silver) en
  vez de Gold — descartado porque cambiaría el contrato ya publicado de
  `casos_unificados.parquet` (001-covid-etl), que solo admite cambios aditivos de columnas, no
  reinterpretaciones de una columna existente; mantener la estandarización en Gold aísla el
  cambio a esta feature.

## 6. Caché y frescura de datos (`@st.cache_data` vs. archivo regenerado)

- **Decision**: Los loaders de `data_loader.py` reciben la ruta del archivo y usan
  `@st.cache_data` con la tupla `(ruta, os.path.getmtime(ruta))` como parte de los argumentos de
  la función cacheada (o `hash_funcs`/parámetro explícito de mtime), de modo que si el pipeline
  Gold se re-ejecuta y el Parquet cambia, la caché se invalida automáticamente en la siguiente
  interacción del usuario, sin necesidad de reiniciar el proceso de Streamlit.
- **Rationale**: `st.cache_data` por defecto solo considera los *valores* de los argumentos como
  clave de caché — si siempre se llama con la misma ruta de string, una regeneración del Parquet
  en disco pasaría desapercibida y la UI mostraría datos obsoletos indefinidamente dentro de la
  misma sesión de servidor. Incluir el mtime del archivo como argumento (o dependencia) fuerza
  una nueva ejecución cuando el archivo cambia, sin sacrificar el beneficio de caché entre
  interacciones de filtro (que no tocan el archivo).
- **Alternatives considered**: `ttl` fijo (ej. 60s) — más simple, pero introduce una ventana de
  datos obsoletos o recargas innecesarias sin relación con si el archivo realmente cambió;
  descartado a favor de la invalidación basada en mtime, más precisa y determinista.

## 7. Resiliencia ante artefactos Gold ausentes o parciales (FR-013)

- **Decision**: Cada función de `data_loader.py` retorna `pd.DataFrame | None` (`None` si el
  archivo no existe), nunca lanza excepción por archivo ausente. `app.py` verifica cada resultado
  antes de renderizar la pestaña/tarjeta correspondiente, mostrando `st.info("... no disponible
  ...")` en su lugar (degradación por pestaña, ver Clarifications en spec.md).
- **Rationale**: Modela el "ausente" como un valor de datos normal (no una condición
  excepcional), simplificando tanto la implementación como las pruebas unitarias de
  `data_loader.py` (no requieren `pytest.raises`, solo aserciones sobre `None`).
- **Alternatives considered**: Lanzar una excepción tipada (`GoldArtifactMissingError`) capturada
  en `app.py` — más ceremonioso para un caso que no es realmente excepcional (la ausencia de un
  archivo Gold individual es un estado esperado durante el rollout incremental de esta feature).

---

## Resultado

Todos los `NEEDS CLARIFICATION` quedan resueltos. No se requieren decisiones adicionales de
investigación antes de proceder al diseño de datos y contratos (Fase 1).
