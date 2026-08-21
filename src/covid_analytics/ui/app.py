"""Tablero epidemiológico interactivo (Streamlit) — entrypoint (FR-001..FR-014).

Orquestación delgada sobre `data_loader.py` (carga) y `filtros.py` (filtrado puro).
Nunca implementa agregaciones nuevas: toda transformación de dimensiones ya ocurrió
en la capa Gold (Principio II).
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from covid_analytics.analytics._shared import tasa_segura
from covid_analytics.cleaning.fechas import FECHA_MAX_VALIDA, FECHA_MIN_VALIDA
from covid_analytics.ui import data_loader
from covid_analytics.ui.filtros import (
    Derechohabiencia,
    FiltroTablero,
    GrupoEdadUi,
    Sexo,
    VistaKPI,
    aplicar_filtro_demografia,
    aplicar_filtro_derechohabiencia,
    aplicar_filtro_series,
    calcular_vista_kpi,
)

_ETIQUETAS_SEXO: dict[str, Sexo] = {"MASCULINO": "M", "FEMENINO": "F"}
_OPCIONES_GRUPO_EDAD: list[GrupoEdadUi] = ["<18", "18-39", "40-59", "60+"]
_OPCIONES_DERECHOHABIENCIA: list[Derechohabiencia] = [
    "IMSS",
    "ISSSTE",
    "ISSEMYM",
    "INSABI",
    "PRIVADO",
    "NINGUNA",
]

_TITULOS_PESTANAS = [
    "Curva Epidemiológica",
    "Demografía & Pirámide",
    "Distribución Geoespacial",
    "Riesgo Clínico",
    "Calidad & Telemetría",
]


def _construir_filtro_sidebar(fecha_min: date, fecha_max: date) -> FiltroTablero:
    if fecha_min < fecha_max:
        fecha_inicio, fecha_fin = st.sidebar.slider(
            "Rango de fechas",
            min_value=fecha_min,
            max_value=fecha_max,
            value=(fecha_min, fecha_max),
            key="filtro_fechas",
        )
    else:
        # Un único día disponible: st.slider exige min_value < max_value.
        st.sidebar.caption(f"Rango de fechas: {fecha_min.isoformat()} (único día disponible)")
        fecha_inicio, fecha_fin = fecha_min, fecha_max
    sexos_ui = st.sidebar.multiselect("Sexo", options=list(_ETIQUETAS_SEXO), key="filtro_sexo")
    grupos_edad_ui = st.sidebar.multiselect(
        "Grupo etario", options=_OPCIONES_GRUPO_EDAD, key="filtro_grupo_edad"
    )
    derechohabiencias = st.sidebar.multiselect(
        "Derechohabiencia", options=_OPCIONES_DERECHOHABIENCIA, key="filtro_derechohabiencia"
    )
    return FiltroTablero(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        sexos=tuple(_ETIQUETAS_SEXO[s] for s in sexos_ui),
        grupos_edad_ui=tuple(grupos_edad_ui),
        derechohabiencias=tuple(derechohabiencias),
    )


def _mover_leyenda_abajo(figura: go.Figure) -> go.Figure:
    """Leyenda horizontal debajo del trazo en vez de lateral.

    Una leyenda lateral le quita hasta la mitad del ancho disponible al
    gráfico en un viewport angosto (celular). Ponerla arriba tampoco sirve:
    en pantallas de ~375px (iPhone XR o menor) los títulos largos en
    español se parten en dos líneas y se encima con la leyenda. Debajo del
    eje X no compite con el título.
    """
    figura.update_layout(
        legend={"orientation": "h", "yanchor": "top", "y": -0.25, "xanchor": "center", "x": 0.5},
        margin={"b": 90},
        title={"automargin": True},
    )
    return figura


def _rotar_etiquetas_categoricas(figura: go.Figure) -> go.Figure:
    """Inclina las etiquetas del eje X para que no se encimen cuando el
    gráfico se angosta (celular)."""
    figura.update_xaxes(tickangle=-30, automargin=True)
    return figura


def _titulo_sin_encimar(figura: go.Figure) -> go.Figure:
    """Deja que Plotly reserve el espacio que el título realmente necesita.

    Sin esto, un título largo en español que se parte en dos líneas en un
    viewport angosto (iPhone XR o menor) se sale del margen fijo y se
    encima con las etiquetas del gráfico.
    """
    figura.update_layout(title={"automargin": True})
    return figura


def _renderizar_kpis(vista: VistaKPI) -> None:
    # st.container(horizontal=True) apila las tarjetas verticalmente en
    # viewports angostos en vez de comprimirlas en 4 columnas ilegibles.
    with st.container(horizontal=True):
        st.metric("Total Pruebas", str(vista.total_pruebas), border=True)
        st.metric(
            "Casos Positivos Confirmados",
            str(vista.casos_positivos_confirmados),
            border=True,
        )
        st.metric(
            "Tasa Global de Positividad", f"{vista.tasa_global_positividad:.1%}", border=True
        )
        st.metric("Tasa de Hospitalización", f"{vista.tasa_hospitalizacion:.1%}", border=True)


def _renderizar_curva_epidemiologica(series_filtrada: pd.DataFrame) -> None:
    if series_filtrada.empty:
        st.info("Sin datos para esta selección.")
        return
    # Excluye días sin casos confirmados: una línea plana en cero comprime la
    # escala del eje Y y aplasta visualmente los picos de las olas.
    con_casos = series_filtrada[series_filtrada["resultados_positivos"] > 0]
    if con_casos.empty:
        st.info("Sin casos positivos confirmados en el rango seleccionado.")
        return
    figura: go.Figure = px.line(
        con_casos,
        x="fecha",
        y=["resultados_positivos", "media_movil_7d_positivos"],
        labels={"value": "Casos", "fecha": "Fecha", "variable": "Serie"},
        title="Casos diarios y media móvil de 7 días",
    )
    _mover_leyenda_abajo(figura)
    st.plotly_chart(figura, width="stretch")


def _renderizar_demografia(demografia_filtrada: pd.DataFrame) -> None:
    if demografia_filtrada.empty:
        st.info("Sin datos para esta selección.")
        return

    piramide = (
        demografia_filtrada.groupby(["grupo_edad_ui", "sexo"], observed=True)["total_casos"]
        .sum()
        .reset_index()
    )
    piramide["casos_mostrados"] = piramide["total_casos"].where(
        piramide["sexo"] != "M", -piramide["total_casos"]
    )
    figura_piramide: go.Figure = px.bar(
        piramide,
        x="casos_mostrados",
        y="grupo_edad_ui",
        color="sexo",
        orientation="h",
        title="Pirámide poblacional (edad × sexo)",
        labels={"casos_mostrados": "Casos", "grupo_edad_ui": "Grupo etario"},
    )
    _mover_leyenda_abajo(figura_piramide)
    st.plotly_chart(figura_piramide, width="stretch")

    con_indicadores = demografia_filtrada.copy()
    con_indicadores["casos_positivos"] = con_indicadores["total_casos"].where(
        con_indicadores["resultado_prueba"] == "POSITIVO", 0
    )
    con_indicadores["casos_negativos"] = con_indicadores["total_casos"].where(
        con_indicadores["resultado_prueba"] == "NEGATIVO", 0
    )
    positividad = (
        con_indicadores.groupby("grupo_edad_ui", observed=True)[
            ["casos_positivos", "casos_negativos"]
        ]
        .sum()
        .reset_index()
    )
    positividad["tasa_positividad"] = positividad.apply(
        lambda f: tasa_segura(f["casos_positivos"], f["casos_positivos"] + f["casos_negativos"]),
        axis=1,
    )
    figura_positividad: go.Figure = px.bar(
        positividad,
        x="grupo_edad_ui",
        y="tasa_positividad",
        title="Tasa de positividad por grupo etario",
        labels={"grupo_edad_ui": "Grupo etario", "tasa_positividad": "Tasa de positividad"},
    )
    _titulo_sin_encimar(figura_positividad)
    st.plotly_chart(figura_positividad, width="stretch")


def _renderizar_geografia(geografia: pd.DataFrame, geojson: dict[str, Any] | None) -> None:
    if geografia.empty:
        st.info("Sin datos para esta selección.")
        return
    features: list[dict[str, Any]] = geojson.get("features", []) if geojson is not None else []
    if not features:
        st.info("Mapa no disponible: falta el shapefile de municipios (`mapa_mexico/*.shp`).")
        return

    datos = geografia.copy()
    datos["municipio_mapa"] = datos["municipio_residencia"].map(
        data_loader.normalizar_municipio_para_mapa
    )
    nombres_disponibles = {f["properties"]["municipio_match"] for f in features}
    datos_con_geometria = datos[datos["municipio_mapa"].isin(nombres_disponibles)]
    municipios_omitidos = sorted(
        set(datos["municipio_residencia"]) - set(datos_con_geometria["municipio_residencia"])
    )

    if datos_con_geometria.empty:
        st.info("Sin datos para esta selección.")
        return

    figura: go.Figure = px.choropleth_map(
        datos_con_geometria,
        geojson=geojson,
        locations="municipio_mapa",
        featureidkey="properties.municipio_match",
        color="total_casos",
        hover_name="municipio_residencia",
        map_style="carto-positron",
        zoom=8,
        center={"lat": 19.5, "lon": -99.0},
        title="Concentración de casos por municipio (zona de influencia)",
        height=700,
    )
    figura.update_layout(margin={"l": 10, "r": 10, "t": 30, "b": 10})
    _titulo_sin_encimar(figura)
    st.plotly_chart(figura, width="stretch")

    if municipios_omitidos:
        st.caption(
            "Municipios sin geometría disponible, omitidos del mapa: "
            + ", ".join(municipios_omitidos)
        )


def _renderizar_riesgo_clinico(derechohabiencia: pd.DataFrame) -> None:
    if derechohabiencia.empty:
        st.info("Sin datos para esta selección.")
        return

    # "OTRA" (catch-all sin catalogar) y "NO_ESPECIFICADO" no aportan valor
    # analítico para comparar derechohabiencias concretas -- se excluyen del
    # renderizado (no de la agregación Gold, que ya los preserva por FR-006a).
    con_valor_analitico = derechohabiencia[
        (derechohabiencia["derechohabiencia"] != "OTRA")
        & (derechohabiencia["resultado_prueba"] != "NO_ESPECIFICADO")
        & (derechohabiencia["total_casos"] > 0)
    ]
    if con_valor_analitico.empty:
        st.info("Sin datos para esta selección.")
        return

    figura_resultado: go.Figure = px.bar(
        con_valor_analitico,
        x="derechohabiencia",
        y="total_casos",
        color="resultado_prueba",
        barmode="group",
        title="Derechohabiencia vs. resultado de prueba",
        labels={"derechohabiencia": "Derechohabiencia", "total_casos": "Casos"},
    )
    _mover_leyenda_abajo(figura_resultado)
    _rotar_etiquetas_categoricas(figura_resultado)
    st.plotly_chart(figura_resultado, width="stretch")

    tasas = con_valor_analitico[
        ["derechohabiencia", "tasa_hospitalizacion_grupo"]
    ].drop_duplicates()
    figura_hospitalizacion: go.Figure = px.bar(
        tasas,
        x="derechohabiencia",
        y="tasa_hospitalizacion_grupo",
        barmode="group",
        title="Tasa de hospitalización por derechohabiencia",
        labels={
            "derechohabiencia": "Derechohabiencia",
            "tasa_hospitalizacion_grupo": "Tasa de hospitalización",
        },
    )
    _rotar_etiquetas_categoricas(figura_hospitalizacion)
    _titulo_sin_encimar(figura_hospitalizacion)
    st.plotly_chart(figura_hospitalizacion, width="stretch")


def _renderizar_calidad(reporte: dict[str, Any] | None) -> None:
    if reporte is None:
        st.info("Reporte de calidad no disponible.")
        return
    st.json(reporte)


def main() -> None:
    st.set_page_config(page_title="Dashboard Epidemiológico — Hospital Gustavo Baz", layout="wide")
    st.title("Dashboard Epidemiológico — Hospital Gustavo Baz")

    demografia = data_loader.cargar_metricas_demografia()
    series = data_loader.cargar_series_temporales()
    geografia = data_loader.cargar_distribucion_geografica()
    kpis = data_loader.cargar_kpis_generales()
    derechohabiencia = data_loader.cargar_metricas_derechohabiencia()

    if demografia is None and series is None and geografia is None and kpis is None:
        st.info("Ejecute el pipeline Gold antes de usar el tablero.")
        return

    fecha_min = FECHA_MIN_VALIDA
    fecha_max = FECHA_MAX_VALIDA
    if series is not None and not series.empty:
        fecha_min = series["fecha"].min().date()
        fecha_max = series["fecha"].max().date()

    filtro = _construir_filtro_sidebar(fecha_min, fecha_max)

    series_filtrada = (
        aplicar_filtro_series(series, filtro) if series is not None else pd.DataFrame()
    )
    demografia_filtrada = (
        aplicar_filtro_demografia(demografia, filtro) if demografia is not None else pd.DataFrame()
    )
    derechohabiencia_filtrada = (
        aplicar_filtro_derechohabiencia(derechohabiencia, filtro)
        if derechohabiencia is not None
        else pd.DataFrame()
    )
    hay_filtro_demografico = bool(filtro.sexos or filtro.grupos_edad_ui)
    hay_filtro_derechohabiencia = bool(filtro.derechohabiencias)

    if kpis is not None or series is not None:
        sin_filtrar = (
            filtro.fecha_inicio == fecha_min
            and filtro.fecha_fin == fecha_max
            and not hay_filtro_demografico
            and not hay_filtro_derechohabiencia
        )
        kpis_df = kpis if kpis is not None else pd.DataFrame()
        vista_kpi = calcular_vista_kpi(
            kpis_df,
            series_filtrada,
            sin_filtrar=sin_filtrar,
            demografia_filtrada=demografia_filtrada if hay_filtro_demografico else None,
            derechohabiencia_filtrada=(
                derechohabiencia_filtrada if hay_filtro_derechohabiencia else None
            ),
        )
        _renderizar_kpis(vista_kpi)
    else:
        st.info("Tarjetas KPI no disponibles: faltan los archivos Gold requeridos.")

    tabs = st.tabs(_TITULOS_PESTANAS)
    with tabs[0]:
        if series is None:
            st.info("Curva epidemiológica no disponible: falta `series_temporales.parquet`.")
        else:
            _renderizar_curva_epidemiologica(series_filtrada)
    with tabs[1]:
        if demografia is None:
            st.info("Demografía no disponible: falta `metricas_demografia.parquet`.")
        else:
            _renderizar_demografia(demografia_filtrada)
    with tabs[2]:
        if geografia is None:
            st.info("Mapa no disponible: falta `distribucion_geografica.parquet`.")
        else:
            _renderizar_geografia(geografia, data_loader.cargar_geojson_municipios())
    with tabs[3]:
        if derechohabiencia is None:
            st.info("Riesgo clínico no disponible: falta `metricas_derechohabiencia.parquet`.")
        else:
            _renderizar_riesgo_clinico(derechohabiencia_filtrada)
    with tabs[4]:
        _renderizar_calidad(data_loader.cargar_reporte_calidad())


main()
