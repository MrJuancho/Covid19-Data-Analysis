import time
from pathlib import Path

from covid_analytics.ui import data_loader
from tests.fixtures.gold_sintetico import escribir_gold_sintetico

_PII_COLUMNS = {"nombre", "telefono", "domicilio", "curp", "paciente_id"}


def test_cargar_metricas_demografia_retorna_none_si_no_existe(tmp_path: Path) -> None:
    assert data_loader.cargar_metricas_demografia(tmp_path / "no_existe.parquet") is None


def test_cargar_metricas_demografia_carga_dataframe(tmp_path: Path) -> None:
    escribir_gold_sintetico(tmp_path)
    df = data_loader.cargar_metricas_demografia(
        tmp_path / "data" / "gold" / "metricas_demografia.parquet"
    )
    assert df is not None
    assert "grupo_edad_ui" in df.columns
    assert not (_PII_COLUMNS & set(df.columns))


def test_cargar_series_temporales_retorna_none_si_no_existe(tmp_path: Path) -> None:
    assert data_loader.cargar_series_temporales(tmp_path / "no_existe.parquet") is None


def test_cargar_series_temporales_carga_dataframe(tmp_path: Path) -> None:
    escribir_gold_sintetico(tmp_path)
    df = data_loader.cargar_series_temporales(
        tmp_path / "data" / "gold" / "series_temporales.parquet"
    )
    assert df is not None
    assert "fecha" in df.columns


def test_cargar_distribucion_geografica_carga_dataframe(tmp_path: Path) -> None:
    escribir_gold_sintetico(tmp_path)
    df = data_loader.cargar_distribucion_geografica(
        tmp_path / "data" / "gold" / "distribucion_geografica.parquet"
    )
    assert df is not None
    assert "municipio_residencia" in df.columns


def test_cargar_kpis_generales_carga_dataframe(tmp_path: Path) -> None:
    escribir_gold_sintetico(tmp_path)
    df = data_loader.cargar_kpis_generales(tmp_path / "data" / "gold" / "kpis_generales.parquet")
    assert df is not None
    assert len(df) == 1


def test_cargar_metricas_derechohabiencia_retorna_none_si_no_existe(tmp_path: Path) -> None:
    assert data_loader.cargar_metricas_derechohabiencia(tmp_path / "no_existe.parquet") is None


def test_cargar_metricas_derechohabiencia_carga_dataframe(tmp_path: Path) -> None:
    escribir_gold_sintetico(tmp_path)
    df = data_loader.cargar_metricas_derechohabiencia(
        tmp_path / "data" / "gold" / "metricas_derechohabiencia.parquet"
    )
    assert df is not None
    assert "derechohabiencia" in df.columns


def test_cargar_reporte_calidad_retorna_none_si_no_existe(tmp_path: Path) -> None:
    assert data_loader.cargar_reporte_calidad(tmp_path / "no_existe.json") is None


def test_cargar_reporte_calidad_retorna_none_si_json_corrupto(tmp_path: Path) -> None:
    ruta = tmp_path / "corrupto.json"
    ruta.write_text("{esto no es json valido", encoding="utf-8")
    assert data_loader.cargar_reporte_calidad(ruta) is None


def test_cargar_reporte_calidad_carga_dict(tmp_path: Path) -> None:
    escribir_gold_sintetico(tmp_path)
    reporte = data_loader.cargar_reporte_calidad(
        tmp_path / "data" / "silver" / "data_quality_summary.json"
    )
    assert reporte is not None
    assert reporte["fechas_anomalas_fuera_ventana"] == 0
    assert not (_PII_COLUMNS & set(reporte.keys()))


def test_cargar_geojson_municipios_retorna_none_si_no_existe(tmp_path: Path) -> None:
    assert data_loader.cargar_geojson_municipios(tmp_path / "no_existe.shp") is None


def test_cargar_geojson_municipios_carga_features_con_municipio_match(tmp_path: Path) -> None:
    escribir_gold_sintetico(tmp_path)
    geojson = data_loader.cargar_geojson_municipios(
        tmp_path / "mapa_mexico" / "Division_Municipal_Mexico_2010.shp"
    )
    assert geojson is not None
    features = geojson["features"]
    assert len(features) == 2
    nombres = {f["properties"]["municipio_match"] for f in features}
    assert "ECATEPEC DE MORELOS" in nombres
    assert "NEZAHUALCOYOTL" in nombres


def test_cargar_metricas_demografia_refleja_archivo_regenerado(tmp_path: Path) -> None:
    escribir_gold_sintetico(tmp_path, demografia=[{"total_casos": 1}])
    ruta = tmp_path / "data" / "gold" / "metricas_demografia.parquet"
    primero = data_loader.cargar_metricas_demografia(ruta)
    assert primero is not None
    assert primero["total_casos"].iloc[0] == 1

    time.sleep(0.05)
    escribir_gold_sintetico(tmp_path, demografia=[{"total_casos": 99}])
    segundo = data_loader.cargar_metricas_demografia(ruta)
    assert segundo is not None
    assert segundo["total_casos"].iloc[0] == 99
