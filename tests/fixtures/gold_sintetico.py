"""Builders de artefactos Gold 100% sintéticos para pruebas de la capa UI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import shapefile

_DEFAULTS_DEMOGRAFIA: dict[str, Any] = {
    "grupo_edad": "31-35",
    "grupo_edad_ui": "18-39",
    "sexo": "F",
    "resultado_prueba": "POSITIVO",
    "estatus_paciente": "AMBULATORIO",
    "total_casos": 1,
    "porcentaje_del_total": 1.0,
    "tasa_positividad_grupo": 1.0,
}

_DEFAULTS_SERIES: dict[str, Any] = {
    "fecha": "2021-01-01",
    "casos_notificados": 1,
    "pruebas_tomadas": 1,
    "resultados_positivos": 1,
    "resultados_negativos": 0,
    "ingresos_hospitalarios": 0,
    "defunciones": 0,
    "media_movil_7d_positivos": 1.0,
    "casos_positivos_acumulados": 1,
}

_DEFAULTS_GEOGRAFIA: dict[str, Any] = {
    "municipio_residencia": "ECATEPEC",
    "total_casos": 10,
    "total_positivos": 5,
    "total_negativos": 5,
    "total_hospitalizados": 1,
    "total_defunciones": 0,
    "tasa_positividad": 0.5,
    "tasa_letalidad": 0.0,
    "tasa_hospitalizacion": 0.2,
}

_DEFAULTS_DERECHOHABIENCIA: dict[str, Any] = {
    "derechohabiencia": "IMSS",
    "resultado_prueba": "POSITIVO",
    "estatus_paciente": "AMBULATORIO",
    "total_casos": 1,
    "porcentaje_del_total": 1.0,
    "tasa_positividad_grupo": 1.0,
    "tasa_hospitalizacion_grupo": 0.0,
    "tasa_letalidad_grupo": 0.0,
}

_DEFAULTS_KPIS: dict[str, Any] = {
    "total_pacientes_atendidos": 10,
    "total_positivos": 5,
    "total_negativos": 5,
    "total_pendientes": 0,
    "total_no_concluyentes": 0,
    "total_hospitalizados": 1,
    "total_defunciones": 0,
    "tasa_global_positividad": 0.5,
    "tasa_global_letalidad": 0.0,
    "tasa_global_hospitalizacion": 0.2,
    "registros_unificados_cruce": 0,
    "mediana_dias_notificacion_ingreso": None,
    "casos_fechas_invertidas": 0,
    "timestamp_generacion": "2026-08-19T00:00:00+00:00",
}

_DEFAULTS_REPORTE_CALIDAD: dict[str, Any] = {
    "filas_leidas_bronze_seguimiento": 10,
    "filas_leidas_bronze_nominal": 8,
    "registros_hasheados": 18,
    "cruces_exitosos": 3,
    "registros_huerfanos": 1,
    "porcentaje_huerfanos": 0.25,
    "correcciones_columnas_intercambiadas": 0,
    "colisiones_llave_sintetica": 0,
    "fechas_anomalas_fuera_ventana": 0,
    "timestamp_ejecucion": "2026-08-19T00:00:00+00:00",
}


def _construir_filas(defaults: dict[str, Any], filas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**defaults, **fila} for fila in filas]


def construir_metricas_demografia_gold(filas: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame.from_records(_construir_filas(_DEFAULTS_DEMOGRAFIA, filas))


def construir_series_temporales_gold(filas: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame.from_records(_construir_filas(_DEFAULTS_SERIES, filas))
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df


def construir_distribucion_geografica_gold(filas: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame.from_records(_construir_filas(_DEFAULTS_GEOGRAFIA, filas))


def construir_metricas_derechohabiencia_gold(filas: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame.from_records(_construir_filas(_DEFAULTS_DERECHOHABIENCIA, filas))


def construir_kpis_generales_gold(**overrides: Any) -> pd.DataFrame:
    return pd.DataFrame.from_records([{**_DEFAULTS_KPIS, **overrides}])


def construir_reporte_calidad(**overrides: Any) -> dict[str, Any]:
    return {**_DEFAULTS_REPORTE_CALIDAD, **overrides}


def _escribir_shapefile_minimo(destino_sin_extension: Path) -> None:
    """Shapefile de prueba con 2 municipios cuadrados, campos NOM_MUN/NOMEDO/CVE_EDO
    compatibles con el shapefile real (`mapa_mexico/Division_Municipal_Mexico_2010.shp`)."""
    with shapefile.Writer(str(destino_sin_extension), shapeType=shapefile.POLYGON) as writer:
        writer.field("CLAVE", "C", size=128)
        writer.field("NOM_MUN", "C", size=28)
        writer.field("NOMEDO", "C", size=21)
        writer.field("CVE_EDO", "C", size=9)
        writer.field("CVE_MUNI", "C", size=10)

        writer.poly([[(-99.1, 19.5), (-99.1, 19.6), (-99.0, 19.6), (-99.0, 19.5), (-99.1, 19.5)]])
        writer.record("15033", "Ecatepec de Morelos", "Mexico", "15", "033")

        writer.poly([[(-99.0, 19.4), (-99.0, 19.5), (-98.9, 19.5), (-98.9, 19.4), (-99.0, 19.4)]])
        writer.record("15058", "Nezahualcoyotl", "Mexico", "15", "058")


def escribir_gold_sintetico(
    base_dir: Path,
    *,
    demografia: list[dict[str, Any]] | None = None,
    series: list[dict[str, Any]] | None = None,
    geografia: list[dict[str, Any]] | None = None,
    derechohabiencia: list[dict[str, Any]] | None = None,
    kpis: dict[str, Any] | None = None,
    reporte_calidad: dict[str, Any] | None = None,
    incluir_derechohabiencia: bool = True,
    incluir_reporte_calidad: bool = True,
    incluir_shapefile: bool = True,
) -> None:
    """Materializa un árbol `data/gold/`, `data/silver/` y `mapa_mexico/` bajo
    `base_dir`, listo para `monkeypatch.chdir(base_dir)` + `AppTest.from_file(...)`.
    """
    gold_dir = base_dir / "data" / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)

    construir_metricas_demografia_gold(demografia or [{}]).to_parquet(
        gold_dir / "metricas_demografia.parquet",
        engine="pyarrow",
        compression="snappy",
        index=False,
    )
    construir_series_temporales_gold(series or [{}]).to_parquet(
        gold_dir / "series_temporales.parquet", engine="pyarrow", compression="snappy", index=False
    )
    construir_distribucion_geografica_gold(geografia or [{}]).to_parquet(
        gold_dir / "distribucion_geografica.parquet",
        engine="pyarrow",
        compression="snappy",
        index=False,
    )
    construir_kpis_generales_gold(**(kpis or {})).to_parquet(
        gold_dir / "kpis_generales.parquet", engine="pyarrow", compression="snappy", index=False
    )

    if incluir_derechohabiencia:
        construir_metricas_derechohabiencia_gold(derechohabiencia or [{}]).to_parquet(
            gold_dir / "metricas_derechohabiencia.parquet",
            engine="pyarrow",
            compression="snappy",
            index=False,
        )

    if incluir_reporte_calidad:
        silver_dir = base_dir / "data" / "silver"
        silver_dir.mkdir(parents=True, exist_ok=True)
        (silver_dir / "data_quality_summary.json").write_text(
            json.dumps(
                construir_reporte_calidad(**(reporte_calidad or {})), indent=2, ensure_ascii=False
            ),
            encoding="utf-8",
        )

    if incluir_shapefile:
        mapa_dir = base_dir / "mapa_mexico"
        mapa_dir.mkdir(parents=True, exist_ok=True)
        _escribir_shapefile_minimo(mapa_dir / "Division_Municipal_Mexico_2010")
