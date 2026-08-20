"""Verifica que fechas fuera de la ventana epidemiológica (typos de año que
se cuelan hasta la capa Silver) no inflen el índice diario continuo de la
capa Gold (`analytics/series_tiempo.py`)."""

import pandas as pd

from covid_analytics.analytics.series_tiempo import calcular_series_temporales
from covid_analytics.cleaning.fechas import FECHA_MAX_VALIDA, FECHA_MIN_VALIDA
from tests.fixtures.silver_sintetico import construir_silver_sintetico


def test_fecha_corrupta_no_infla_el_indice_temporal() -> None:
    filas = [
        {
            "fecha_notificacion": "2021-05-15",
            "fecha_resultado": "2021-05-17",
            "resultado_prueba": "POSITIVO",
        },
        {
            # Typo de captura: año "0202" en vez de "2020" (research.md /
            # cleaning/fechas.py). Si esta fecha se usara sin acotar, el
            # índice diario se extendería ~1800 años hacia atrás.
            "fecha_notificacion": "0202-05-15",
            "fecha_resultado": "0202-05-17",
            "resultado_prueba": "NEGATIVO",
        },
    ]
    df = construir_silver_sintetico(filas)
    serie, _ = calcular_series_temporales(df)

    ventana_dias = (FECHA_MAX_VALIDA - FECHA_MIN_VALIDA).days + 1
    assert len(serie) <= ventana_dias
    assert len(serie) < 400  # el rango real de este fixture es de días, no de siglos
    assert serie["fecha"].min() >= pd.Timestamp(FECHA_MIN_VALIDA)
    assert serie["fecha"].max() <= pd.Timestamp(FECHA_MAX_VALIDA)


def test_fecha_muy_futura_no_infla_el_indice_temporal() -> None:
    filas = [
        {
            "fecha_notificacion": "2021-05-15",
            "fecha_resultado": "2021-05-17",
            "resultado_prueba": "POSITIVO",
        },
        {
            "fecha_notificacion": "2920-05-15",  # typo de "2020"
            "resultado_prueba": "NEGATIVO",
        },
    ]
    df = construir_silver_sintetico(filas)
    serie, _ = calcular_series_temporales(df)

    assert len(serie) < 400


def test_todas_las_fechas_fuera_de_ventana_produce_serie_vacia() -> None:
    filas = [{"fecha_notificacion": "0208-05-15", "resultado_prueba": "POSITIVO"}]
    df = construir_silver_sintetico(filas)
    serie, _ = calcular_series_temporales(df)
    assert len(serie) == 0
