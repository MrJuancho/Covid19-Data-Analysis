"""Series temporales continuas y curvas epidemiológicas (FR-004, FR-004a, US2)."""

from __future__ import annotations

import pandas as pd

from covid_analytics.cleaning.fechas import FECHA_MAX_VALIDA, FECHA_MIN_VALIDA

_COLUMNAS_FECHA_INDICE = [
    "fecha_notificacion",
    "fecha_toma_muestra",
    "fecha_resultado",
    "fecha_ingreso_hospital",
]

# Defensa en profundidad: aunque `cleaning/fechas.py` ya descarta como NaT
# cualquier fecha fuera de la ventana epidemiológica al construir la capa
# Silver, el índice diario se acota aquí también por si un Parquet Silver
# más antiguo (generado antes de ese fix) o una fuente externa aporta una
# fecha corrupta -- sin esto, un solo typo de año infla el índice a cientos
# de miles de filas (ej. año "0202" en vez de "2020").
_VENTANA_MIN = pd.Timestamp(FECHA_MIN_VALIDA)
_VENTANA_MAX = pd.Timestamp(FECHA_MAX_VALIDA)


def _conteo_diario(fechas: pd.Series, indice: pd.DatetimeIndex) -> pd.Series:
    conteo = fechas.dropna().dt.normalize().value_counts()
    resultado: pd.Series = conteo.reindex(indice, fill_value=0).astype("int64")
    return resultado


def calcular_series_temporales(df_silver: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Genera la serie diaria continua de la capa Gold (FR-004).

    Detecta anomalías de `fecha_resultado` anterior a `fecha_toma_muestra`
    (FR-004a) como telemetría (`casos_fechas_invertidas`), sin excluir esos
    casos de los conteos diarios: excluirlos rompería la consistencia
    marginal exacta exigida por FR-007 entre `series_temporales` y las demás
    tablas Gold.
    """
    fechas_relevantes = pd.concat([df_silver[col] for col in _COLUMNAS_FECHA_INDICE]).dropna()
    fechas_relevantes = fechas_relevantes[
        (fechas_relevantes >= _VENTANA_MIN) & (fechas_relevantes <= _VENTANA_MAX)
    ]

    if fechas_relevantes.empty:
        indice = pd.DatetimeIndex([], name="fecha")
    else:
        indice = pd.date_range(
            fechas_relevantes.min().normalize(),
            fechas_relevantes.max().normalize(),
            freq="D",
            name="fecha",
        )

    es_positivo = df_silver["resultado_prueba"] == "POSITIVO"
    es_negativo = df_silver["resultado_prueba"] == "NEGATIVO"
    # Asunción de diseño: las defunciones se telemetrizan por fecha_notificacion,
    # la fecha con menor probabilidad de estar ausente en el registro (research.md).
    es_defuncion = df_silver["estatus_paciente"] == "DEFUNCION"

    serie = pd.DataFrame(index=indice)
    serie["casos_notificados"] = _conteo_diario(df_silver["fecha_notificacion"], indice)
    serie["pruebas_tomadas"] = _conteo_diario(df_silver["fecha_toma_muestra"], indice)
    serie["resultados_positivos"] = _conteo_diario(
        df_silver.loc[es_positivo, "fecha_resultado"], indice
    )
    serie["resultados_negativos"] = _conteo_diario(
        df_silver.loc[es_negativo, "fecha_resultado"], indice
    )
    serie["ingresos_hospitalarios"] = _conteo_diario(df_silver["fecha_ingreso_hospital"], indice)
    serie["defunciones"] = _conteo_diario(df_silver.loc[es_defuncion, "fecha_notificacion"], indice)

    serie["media_movil_7d_positivos"] = (
        serie["resultados_positivos"].rolling(window=7, min_periods=1).mean()
    )
    serie["casos_positivos_acumulados"] = serie["resultados_positivos"].cumsum()

    fechas_invertidas = (
        df_silver["fecha_resultado"].notna()
        & df_silver["fecha_toma_muestra"].notna()
        & (df_silver["fecha_resultado"] < df_silver["fecha_toma_muestra"])
    )
    casos_fechas_invertidas = int(fechas_invertidas.sum())

    return serie.reset_index(), casos_fechas_invertidas
