"""Carga resiliente y cacheada de artefactos Gold para el tablero (FR-001, FR-002, FR-013).

Ninguna función de este módulo lee `data/bronze/*` ni columnas con identificadores
individuales de paciente. La única excepción es `cargar_reporte_calidad`, que lee
`data/silver/data_quality_summary.json` (telemetría agregada sin PII, 001-covid-etl).
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
import shapefile
import streamlit as st

_RUTA_METRICAS_DEMOGRAFIA = Path("data/gold/metricas_demografia.parquet")
_RUTA_SERIES_TEMPORALES = Path("data/gold/series_temporales.parquet")
_RUTA_DISTRIBUCION_GEOGRAFICA = Path("data/gold/distribucion_geografica.parquet")
_RUTA_KPIS_GENERALES = Path("data/gold/kpis_generales.parquet")
_RUTA_METRICAS_DERECHOHABIENCIA = Path("data/gold/metricas_derechohabiencia.parquet")
_RUTA_REPORTE_CALIDAD = Path("data/silver/data_quality_summary.json")
_RUTA_SHAPEFILE_MUNICIPIOS = Path("mapa_mexico/Division_Municipal_Mexico_2010.shp")

# Estados que cubren el catálogo de municipios de `cleaning/catalogos.py` (Ciudad de
# México "D.F." y Estado de México "MEXICO" en el shapefile). Acotar por estado evita
# colisiones de nombre entre municipios homónimos de otros estados (ej. "La Paz"
# también existe en Baja California Sur).
_ESTADOS_ZONA_INFLUENCIA = {"D.F.", "MEXICO"}

# Alias entre el catálogo canónico de Gold (cleaning/catalogos.py) y el nombre completo
# usado en el shapefile, para los municipios donde difieren.
_ALIAS_MUNICIPIO_SHAPEFILE: dict[str, str] = {
    "ECATEPEC": "ECATEPEC DE MORELOS",
    "TLALNEPANTLA": "TLALNEPANTLA DE BAZ",
    "NAUCALPAN": "NAUCALPAN DE JUAREZ",
}


def normalizar_municipio_para_mapa(municipio_residencia: str) -> str:
    """Traduce un `municipio_residencia` canónico de Gold al nombre usado en el
    shapefile (`municipio_match`), para el join de la Pestaña 3 (US3)."""
    return _ALIAS_MUNICIPIO_SHAPEFILE.get(municipio_residencia, municipio_residencia)


def _normalizar_texto(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", texto.upper().strip())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


@st.cache_data(show_spinner=False)
def _leer_parquet_cacheado(ruta_str: str, mtime: float) -> pd.DataFrame:
    resultado: pd.DataFrame = pd.read_parquet(ruta_str)
    return resultado


def _cargar_parquet_resiliente(ruta: Path) -> pd.DataFrame | None:
    if not ruta.exists():
        return None
    return _leer_parquet_cacheado(str(ruta), ruta.stat().st_mtime)


def cargar_metricas_demografia(ruta: Path = _RUTA_METRICAS_DEMOGRAFIA) -> pd.DataFrame | None:
    return _cargar_parquet_resiliente(ruta)


def cargar_series_temporales(ruta: Path = _RUTA_SERIES_TEMPORALES) -> pd.DataFrame | None:
    return _cargar_parquet_resiliente(ruta)


def cargar_distribucion_geografica(
    ruta: Path = _RUTA_DISTRIBUCION_GEOGRAFICA,
) -> pd.DataFrame | None:
    return _cargar_parquet_resiliente(ruta)


def cargar_kpis_generales(ruta: Path = _RUTA_KPIS_GENERALES) -> pd.DataFrame | None:
    return _cargar_parquet_resiliente(ruta)


def cargar_metricas_derechohabiencia(
    ruta: Path = _RUTA_METRICAS_DERECHOHABIENCIA,
) -> pd.DataFrame | None:
    return _cargar_parquet_resiliente(ruta)


@st.cache_data(show_spinner=False)
def _leer_json_cacheado(ruta_str: str, mtime: float) -> dict[str, Any] | None:
    try:
        contenido: dict[str, Any] = json.loads(Path(ruta_str).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return contenido


def cargar_reporte_calidad(ruta: Path = _RUTA_REPORTE_CALIDAD) -> dict[str, Any] | None:
    if not ruta.exists():
        return None
    return _leer_json_cacheado(str(ruta), ruta.stat().st_mtime)


@st.cache_resource(show_spinner=False)
def _leer_geojson_cacheado(ruta_str: str, mtime: float) -> dict[str, Any]:
    ruta_base = str(Path(ruta_str).with_suffix(""))
    lector = shapefile.Reader(ruta_base, encoding="latin-1")
    features: list[dict[str, Any]] = []
    for forma in lector.shapeRecords():
        atributos = forma.record.as_dict()
        estado = _normalizar_texto(str(atributos.get("NOMEDO", "")))
        if estado not in _ESTADOS_ZONA_INFLUENCIA:
            continue
        geojson_forma: dict[str, Any] = forma.shape.__geo_interface__
        features.append(
            {
                "type": "Feature",
                "geometry": geojson_forma,
                "properties": {
                    "municipio_match": _normalizar_texto(str(atributos.get("NOM_MUN", ""))),
                },
                "id": _normalizar_texto(str(atributos.get("NOM_MUN", ""))),
            }
        )
    return {"type": "FeatureCollection", "features": features}


def cargar_geojson_municipios(ruta: Path = _RUTA_SHAPEFILE_MUNICIPIOS) -> dict[str, Any] | None:
    if not ruta.exists():
        return None
    return _leer_geojson_cacheado(str(ruta), ruta.stat().st_mtime)
