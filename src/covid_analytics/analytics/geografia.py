"""Distribución geográfica y tasas municipales (FR-005, US3)."""

from __future__ import annotations

import pandas as pd

from covid_analytics.analytics._shared import tasa_segura

_COLUMNAS_SALIDA = [
    "municipio_residencia",
    "total_casos",
    "total_positivos",
    "total_negativos",
    "total_hospitalizados",
    "total_defunciones",
    "tasa_positividad",
    "tasa_letalidad",
    "tasa_hospitalizacion",
]


def calcular_distribucion_geografica(df_silver: pd.DataFrame) -> pd.DataFrame:
    """Agrega por `municipio_residencia`, calculando tasas seguras ante
    denominador `0` (FR-005)."""
    df = df_silver.assign(
        es_positivo=df_silver["resultado_prueba"] == "POSITIVO",
        es_negativo=df_silver["resultado_prueba"] == "NEGATIVO",
        es_hospitalizado=df_silver["estatus_paciente"] == "HOSPITALIZADO",
        es_defuncion=df_silver["estatus_paciente"] == "DEFUNCION",
    )
    df["es_defuncion_positiva"] = df["es_positivo"] & df["es_defuncion"]
    df["es_hospitalizado_positivo"] = df["es_positivo"] & df["es_hospitalizado"]

    agregado = (
        df.groupby("municipio_residencia", observed=True)
        .agg(
            total_casos=("municipio_residencia", "size"),
            total_positivos=("es_positivo", "sum"),
            total_negativos=("es_negativo", "sum"),
            total_hospitalizados=("es_hospitalizado", "sum"),
            total_defunciones=("es_defuncion", "sum"),
            defunciones_positivas=("es_defuncion_positiva", "sum"),
            hospitalizados_positivos=("es_hospitalizado_positivo", "sum"),
        )
        .reset_index()
    )

    agregado["tasa_positividad"] = agregado.apply(
        lambda fila: tasa_segura(
            fila["total_positivos"], fila["total_positivos"] + fila["total_negativos"]
        ),
        axis=1,
    )
    agregado["tasa_letalidad"] = agregado.apply(
        lambda fila: tasa_segura(fila["defunciones_positivas"], fila["total_positivos"]), axis=1
    )
    agregado["tasa_hospitalizacion"] = agregado.apply(
        lambda fila: tasa_segura(fila["hospitalizados_positivos"], fila["total_positivos"]), axis=1
    )

    for columna in (
        "total_casos",
        "total_positivos",
        "total_negativos",
        "total_hospitalizados",
        "total_defunciones",
    ):
        agregado[columna] = agregado[columna].astype("int64")

    return agregado[_COLUMNAS_SALIDA]
