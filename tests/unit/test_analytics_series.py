import pandas as pd

from covid_analytics.analytics.series_tiempo import calcular_series_temporales
from tests.fixtures.silver_sintetico import construir_silver_sintetico


def test_calcular_series_temporales_genera_indice_diario_continuo() -> None:
    filas = [
        {
            "fecha_notificacion": "2021-01-01",
            "fecha_toma_muestra": "2021-01-01",
            "fecha_resultado": "2021-01-03",
            "resultado_prueba": "POSITIVO",
        },
        {
            "fecha_notificacion": "2021-01-05",
            "fecha_toma_muestra": "2021-01-05",
            "fecha_resultado": "2021-01-07",
            "resultado_prueba": "NEGATIVO",
        },
    ]
    df = construir_silver_sintetico(filas)
    serie, _ = calcular_series_temporales(df)

    assert len(serie) == 7  # 2021-01-01 .. 2021-01-07 inclusive, sin huecos
    assert serie["fecha"].is_monotonic_increasing
    dias_con_actividad = pd.to_datetime(["2021-01-01", "2021-01-05"])
    dias_sin_actividad = serie[~serie["fecha"].isin(dias_con_actividad)]
    assert (dias_sin_actividad["casos_notificados"] == 0).all()


def test_calcular_series_temporales_media_movil_7d_min_periods_1() -> None:
    filas = [
        {
            "fecha_notificacion": "2021-01-01",
            "fecha_resultado": "2021-01-01",
            "resultado_prueba": "POSITIVO",
        }
    ]
    df = construir_silver_sintetico(filas)
    serie, _ = calcular_series_temporales(df)

    assert len(serie) == 1
    assert serie["media_movil_7d_positivos"].iloc[0] == 1.0
    assert serie["casos_positivos_acumulados"].iloc[0] == 1


def test_calcular_series_temporales_acumulado_creciente() -> None:
    filas = [
        {
            "fecha_notificacion": "2021-01-01",
            "fecha_resultado": "2021-01-01",
            "resultado_prueba": "POSITIVO",
        },
        {
            "fecha_notificacion": "2021-01-02",
            "fecha_resultado": "2021-01-02",
            "resultado_prueba": "POSITIVO",
        },
        {
            "fecha_notificacion": "2021-01-03",
            "fecha_resultado": "2021-01-03",
            "resultado_prueba": "NEGATIVO",
        },
    ]
    df = construir_silver_sintetico(filas)
    serie, _ = calcular_series_temporales(df)

    assert serie["casos_positivos_acumulados"].tolist() == [1, 2, 2]


def test_calcular_series_temporales_detecta_fechas_invertidas_sin_excluir_conteos() -> None:
    filas = [
        {
            "fecha_notificacion": "2021-01-01",
            "fecha_toma_muestra": "2021-01-05",
            "fecha_resultado": "2021-01-01",  # resultado antes de la toma de muestra
            "resultado_prueba": "POSITIVO",
        },
        {
            "fecha_notificacion": "2021-01-01",
            "fecha_toma_muestra": "2021-01-01",
            "fecha_resultado": "2021-01-03",
            "resultado_prueba": "POSITIVO",
        },
    ]
    df = construir_silver_sintetico(filas)
    serie, casos_fechas_invertidas = calcular_series_temporales(df)

    assert casos_fechas_invertidas == 1
    # La anomalía se telemetriza, pero el caso sigue contando en su día de resultado
    # (consistencia marginal exacta con las demás tablas Gold, FR-007).
    assert serie["resultados_positivos"].sum() == 2


def test_calcular_series_temporales_dataset_vacio_no_falla() -> None:
    df = construir_silver_sintetico([])
    serie, casos_fechas_invertidas = calcular_series_temporales(df)
    assert len(serie) == 0
    assert casos_fechas_invertidas == 0
