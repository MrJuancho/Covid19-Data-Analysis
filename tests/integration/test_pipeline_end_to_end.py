import json
from pathlib import Path

import pandas as pd

from covid_analytics.pipeline import ejecutar_pipeline
from tests.fixtures.excel_sintetico import construir_excel_sintetico

_PII_COLUMNS = {"CASO", "NOMBRE DEL PACIENTE", "CALLE", "TELEFONO"}

_COLUMNAS_ESPERADAS = {
    "paciente_id",
    "edad",
    "sexo",
    "municipio_residencia",
    "derechohabiencia",
    "fecha_notificacion",
    "fecha_toma_muestra",
    "fecha_resultado",
    "resultado_prueba",
    "estatus_paciente",
    "es_registro_unificado",
    "dias_entre_notificacion_e_ingreso",
}


def test_pipeline_completo_escribe_parquet_y_json(tmp_path: Path) -> None:
    filas_seguimiento = [
        {
            "NO. (consecutivo)": 1,
            "CASO (nombre,apellido paterno, apellido materno)": "Paciente Uno Sintetico",
            "SEXO (M/F)": "F",
            "EDAD (ej: anos: 3;meses-3M)": "34",
            "FECHA DE NOTIFICACION (dd/mm/aaaa)": "18/03/2020",
            "RESULTADO (POSITIVO, NEGATIVO, PENDIENTE)": "POSITIVO",
        }
    ]
    filas_nominal = [
        {
            "HOSPITAL": "Hospital Sintetico",
            "NO.": 2,
            "NOMBRE DEL PACIENTE": "Paciente Dos Sintetico",
            "F": "40",
            "FECHA DE INGRESO O DE ATENCION": "22/03/2020",
        }
    ]
    excel = construir_excel_sintetico(tmp_path / "sintetico.xlsx", filas_seguimiento, filas_nominal)
    output_dir = tmp_path / "salida"

    ejecutar_pipeline(excel, output_dir, salt="sal-test")

    ruta_parquet = output_dir / "casos_unificados.parquet"
    ruta_json = output_dir / "data_quality_summary.json"
    assert ruta_parquet.exists()
    assert ruta_json.exists()

    df = pd.read_parquet(ruta_parquet)
    assert _COLUMNAS_ESPERADAS <= set(df.columns)
    assert df["paciente_id"].str.len().eq(64).all()
    assert not (_PII_COLUMNS & set(df.columns))
    assert len(df) == 2

    resumen = json.loads(ruta_json.read_text(encoding="utf-8"))
    assert all(v is not None for v in resumen.values())
    assert resumen["filas_leidas_bronze_seguimiento"] == 1
    assert resumen["filas_leidas_bronze_nominal"] == 1


def test_pipeline_layer_gold_genera_tambien_la_capa_gold(tmp_path: Path) -> None:
    filas_seguimiento = [
        {
            "NO. (consecutivo)": 1,
            "CASO (nombre,apellido paterno, apellido materno)": "Paciente Uno Sintetico",
            "SEXO (M/F)": "F",
            "EDAD (ej: anos: 3;meses-3M)": "34",
            "FECHA DE NOTIFICACION (dd/mm/aaaa)": "18/03/2020",
            "RESULTADO (POSITIVO, NEGATIVO, PENDIENTE)": "POSITIVO",
        }
    ]
    excel = construir_excel_sintetico(tmp_path / "sintetico.xlsx", filas_seguimiento, [])
    silver_dir = tmp_path / "silver"
    gold_dir = tmp_path / "gold"

    ejecutar_pipeline(excel, silver_dir, salt="sal-test", layer="gold", gold_output_dir=gold_dir)

    assert (silver_dir / "casos_unificados.parquet").exists()
    assert (gold_dir / "kpis_generales.parquet").exists()
    assert (gold_dir / "resumen_ejecutivo.json").exists()

    kpis = json.loads((gold_dir / "resumen_ejecutivo.json").read_text(encoding="utf-8"))
    assert kpis["total_pacientes_atendidos"] == 1
