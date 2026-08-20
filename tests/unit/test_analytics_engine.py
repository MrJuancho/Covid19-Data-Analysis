import json
import time
from pathlib import Path

import pandas as pd
import pytest

from covid_analytics.analytics import engine
from covid_analytics.analytics._shared import GoldIntegrityError
from covid_analytics.analytics.demografia import calcular_metricas_demografia
from covid_analytics.analytics.derechohabiencia import calcular_metricas_derechohabiencia
from covid_analytics.analytics.engine import (
    calcular_kpis_generales,
    generar_capa_gold,
    verificar_consistencia_marginal,
)
from covid_analytics.analytics.geografia import calcular_distribucion_geografica
from covid_analytics.analytics.series_tiempo import calcular_series_temporales
from tests.fixtures.silver_sintetico import construir_silver_sintetico, generar_dataset_variado

_PII_COLUMNS = {"nombre", "telefono", "domicilio", "curp", "paciente_id"}


def test_generar_capa_gold_escribe_todos_los_archivos(tmp_path: Path) -> None:
    df = generar_dataset_variado(n_dias=10, casos_por_dia=3)
    generar_capa_gold(df, tmp_path)

    for nombre in (
        "metricas_demografia.parquet",
        "series_temporales.parquet",
        "distribucion_geografica.parquet",
        "kpis_generales.parquet",
        "metricas_derechohabiencia.parquet",
        "resumen_ejecutivo.json",
    ):
        assert (tmp_path / nombre).exists()

    resumen = json.loads((tmp_path / "resumen_ejecutivo.json").read_text(encoding="utf-8"))
    assert resumen["total_pacientes_atendidos"] == len(df)
    assert resumen["casos_fechas_invertidas"] >= 1


def test_generar_capa_gold_consistencia_positivos_entre_tablas(tmp_path: Path) -> None:
    df = generar_dataset_variado(n_dias=15, casos_por_dia=5)
    generar_capa_gold(df, tmp_path)

    demografia = pd.read_parquet(tmp_path / "metricas_demografia.parquet")
    series = pd.read_parquet(tmp_path / "series_temporales.parquet")
    geografia = pd.read_parquet(tmp_path / "distribucion_geografica.parquet")
    kpis = pd.read_parquet(tmp_path / "kpis_generales.parquet")
    derechohabiencia = pd.read_parquet(tmp_path / "metricas_derechohabiencia.parquet")

    total_positivos_silver = int((df["resultado_prueba"] == "POSITIVO").sum())
    assert (
        demografia.loc[demografia["resultado_prueba"] == "POSITIVO", "total_casos"].sum()
        == total_positivos_silver
    )
    assert series["resultados_positivos"].sum() == total_positivos_silver
    assert geografia["total_positivos"].sum() == total_positivos_silver
    assert kpis["total_positivos"].iloc[0] == total_positivos_silver
    assert (
        derechohabiencia.loc[
            derechohabiencia["resultado_prueba"] == "POSITIVO", "total_casos"
        ].sum()
        == total_positivos_silver
    )

    assert demografia["total_casos"].sum() == len(df)
    assert geografia["total_casos"].sum() == len(df)
    assert kpis["total_pacientes_atendidos"].iloc[0] == len(df)
    assert derechohabiencia["total_casos"].sum() == len(df)


def test_generar_capa_gold_no_contiene_columnas_pii(tmp_path: Path) -> None:
    df = generar_dataset_variado(n_dias=5, casos_por_dia=2)
    generar_capa_gold(df, tmp_path)

    for nombre in (
        "metricas_demografia.parquet",
        "series_temporales.parquet",
        "distribucion_geografica.parquet",
        "kpis_generales.parquet",
        "metricas_derechohabiencia.parquet",
    ):
        tabla = pd.read_parquet(tmp_path / nombre)
        assert not (_PII_COLUMNS & set(tabla.columns)), f"PII detectado en {nombre}"


def test_calcular_kpis_generales_campos_basicos() -> None:
    filas = [
        {"resultado_prueba": "POSITIVO", "estatus_paciente": "DEFUNCION"},
        {"resultado_prueba": "POSITIVO", "estatus_paciente": "HOSPITALIZADO"},
        {"resultado_prueba": "NEGATIVO", "estatus_paciente": "AMBULATORIO"},
        {
            "resultado_prueba": "POSITIVO",
            "estatus_paciente": "HOSPITALIZADO",
            "es_registro_unificado": True,
            "dias_entre_notificacion_e_ingreso": 3,
        },
    ]
    df = construir_silver_sintetico(filas)
    kpis = calcular_kpis_generales(df, casos_fechas_invertidas=2)

    assert kpis.total_pacientes_atendidos == 4
    assert kpis.total_positivos == 3
    assert kpis.total_negativos == 1
    assert kpis.registros_unificados_cruce == 1
    assert kpis.mediana_dias_notificacion_ingreso == 3.0
    assert kpis.casos_fechas_invertidas == 2
    assert round(kpis.tasa_global_letalidad, 4) == round(1 / 3, 4)
    assert round(kpis.tasa_global_hospitalizacion, 4) == round(2 / 3, 4)


def test_calcular_kpis_generales_mediana_nula_sin_cruces() -> None:
    df = construir_silver_sintetico([{"resultado_prueba": "NEGATIVO"}])
    kpis = calcular_kpis_generales(df, casos_fechas_invertidas=0)
    assert kpis.mediana_dias_notificacion_ingreso is None


def test_verificar_consistencia_marginal_detecta_inconsistencia() -> None:
    df = generar_dataset_variado(n_dias=5, casos_por_dia=2)
    demografia = calcular_metricas_demografia(df)
    series, casos_fechas_invertidas = calcular_series_temporales(df)
    geografia = calcular_distribucion_geografica(df)
    derechohabiencia = calcular_metricas_derechohabiencia(df)
    kpis = calcular_kpis_generales(df, casos_fechas_invertidas=casos_fechas_invertidas)

    # Corrompemos deliberadamente la tabla demográfica para violar FR-007.
    demografia_corrupta = demografia.copy()
    demografia_corrupta.loc[demografia_corrupta.index[0], "total_casos"] += 1

    with pytest.raises(GoldIntegrityError):
        verificar_consistencia_marginal(
            df, demografia_corrupta, series, geografia, kpis, derechohabiencia
        )

    # La versión no corrompida no debe lanzar.
    verificar_consistencia_marginal(df, demografia, series, geografia, kpis, derechohabiencia)


def test_main_exit_code_1_si_falta_archivo_silver(tmp_path: Path) -> None:
    codigo = engine.main(
        [
            "--silver-path",
            str(tmp_path / "no_existe.parquet"),
            "--output-dir",
            str(tmp_path / "gold"),
        ]
    )
    assert codigo == 1


def test_main_exit_code_1_si_esquema_invalido(tmp_path: Path) -> None:
    df = construir_silver_sintetico([{"resultado_prueba": "POSITIVO"}]).drop(
        columns=["paciente_id"]
    )
    silver_path = tmp_path / "casos_unificados.parquet"
    df.to_parquet(silver_path, engine="pyarrow", compression="snappy", index=False)

    codigo = engine.main(
        ["--silver-path", str(silver_path), "--output-dir", str(tmp_path / "gold")]
    )
    assert codigo == 1


def test_main_exit_code_0_caso_exitoso(tmp_path: Path) -> None:
    df = generar_dataset_variado(n_dias=5, casos_por_dia=2)
    silver_path = tmp_path / "casos_unificados.parquet"
    df.to_parquet(silver_path, engine="pyarrow", compression="snappy", index=False)
    output_dir = tmp_path / "gold"

    codigo = engine.main(["--silver-path", str(silver_path), "--output-dir", str(output_dir)])
    assert codigo == 0
    assert (output_dir / "kpis_generales.parquet").exists()


def test_main_exit_code_2_ante_error_de_integridad(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    df = generar_dataset_variado(n_dias=3, casos_por_dia=2)
    silver_path = tmp_path / "casos_unificados.parquet"
    df.to_parquet(silver_path, engine="pyarrow", compression="snappy", index=False)

    def _falla(*_args: object, **_kwargs: object) -> None:
        raise GoldIntegrityError("inconsistencia simulada")

    monkeypatch.setattr(engine, "generar_capa_gold", _falla)

    codigo = engine.main(
        ["--silver-path", str(silver_path), "--output-dir", str(tmp_path / "gold")]
    )
    assert codigo == 2


def test_generar_capa_gold_rendimiento_bajo_5_segundos(tmp_path: Path) -> None:
    df = generar_dataset_variado(n_dias=180, casos_por_dia=20)
    inicio = time.perf_counter()
    generar_capa_gold(df, tmp_path)
    duracion = time.perf_counter() - inicio
    assert duracion < 5.0
