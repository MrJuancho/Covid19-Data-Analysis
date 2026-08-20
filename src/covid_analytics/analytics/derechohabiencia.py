"""Cruce de derechohabiencia vs. positividad/hospitalización/letalidad (FR-006a, US4)."""

from __future__ import annotations

import unicodedata

import pandas as pd

from covid_analytics.analytics._shared import tasa_segura

_OTRA = "OTRA"

# FR-006a: `derechohabiencia` es texto libre en Silver (sentinel "NINGUNO",
# sin catálogo cerrado); se estandariza aquí al catálogo de 6 categorías
# pedidas por el sidebar más `OTRA` para cualquier valor no reconocido
# (ej. "SEDENA"), análogo a `municipio_residencia` -> `"OTROS"` en
# `cleaning/catalogos.py` (001/002-covid-etl).
CATALOGO_DERECHOHABIENCIA: list[str] = [
    "IMSS",
    "ISSSTE",
    "ISSEMYM",
    "INSABI",
    "PRIVADO",
    "NINGUNA",
    _OTRA,
]

_SINONIMOS: dict[str, str] = {
    "IMSS": "IMSS",
    "ISSSTE": "ISSSTE",
    "ISSEMYM": "ISSEMYM",
    "INSABI": "INSABI",
    "PRIVADO": "PRIVADO",
    "PRIVADA": "PRIVADO",
    "NINGUNO": "NINGUNA",
    "NINGUNA": "NINGUNA",
}


def _normalizar_texto(texto: str) -> str:
    mayusculas = texto.upper()
    descompuesto = unicodedata.normalize("NFD", mayusculas)
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return " ".join(sin_acentos.split())


def estandarizar_derechohabiencia(valor: str | None) -> str:
    """Mapea `valor` (texto libre de Silver) al catálogo cerrado de 7
    categorías (`CATALOGO_DERECHOHABIENCIA`); cualquier valor no reconocido
    (ej. `SEDENA`) cae en `OTRA`."""
    if valor is None:
        return "NINGUNA"
    return _SINONIMOS.get(_normalizar_texto(valor), _OTRA)


def calcular_metricas_derechohabiencia(df_silver: pd.DataFrame) -> pd.DataFrame:
    """Cubo (derechohabiencia x resultado_prueba x estatus_paciente) con
    conteos, participación porcentual y tasas de positividad/hospitalización/
    letalidad por grupo de derechohabiencia (FR-006a)."""
    df = df_silver.copy()
    df["derechohabiencia"] = df["derechohabiencia"].map(estandarizar_derechohabiencia)
    df["es_positivo"] = df["resultado_prueba"] == "POSITIVO"
    df["es_negativo"] = df["resultado_prueba"] == "NEGATIVO"
    df["es_hospitalizado_positivo"] = df["es_positivo"] & (
        df["estatus_paciente"] == "HOSPITALIZADO"
    )
    df["es_defuncion_positiva"] = df["es_positivo"] & (df["estatus_paciente"] == "DEFUNCION")

    cubo = (
        df.groupby(["derechohabiencia", "resultado_prueba", "estatus_paciente"], observed=True)
        .size()
        .rename("total_casos")
        .reset_index()
    )

    total_global = len(df_silver)
    cubo["porcentaje_del_total"] = cubo["total_casos"] / total_global if total_global > 0 else 0.0

    agregados_grupo = (
        df.groupby("derechohabiencia", observed=True)
        .agg(
            positivos=("es_positivo", "sum"),
            negativos=("es_negativo", "sum"),
            hospitalizados_positivos=("es_hospitalizado_positivo", "sum"),
            defunciones_positivas=("es_defuncion_positiva", "sum"),
        )
        .reset_index()
    )
    agregados_grupo["tasa_positividad_grupo"] = agregados_grupo.apply(
        lambda f: tasa_segura(f["positivos"], f["positivos"] + f["negativos"]), axis=1
    )
    agregados_grupo["tasa_hospitalizacion_grupo"] = agregados_grupo.apply(
        lambda f: tasa_segura(f["hospitalizados_positivos"], f["positivos"]), axis=1
    )
    agregados_grupo["tasa_letalidad_grupo"] = agregados_grupo.apply(
        lambda f: tasa_segura(f["defunciones_positivas"], f["positivos"]), axis=1
    )

    cubo = cubo.merge(
        agregados_grupo[
            [
                "derechohabiencia",
                "tasa_positividad_grupo",
                "tasa_hospitalizacion_grupo",
                "tasa_letalidad_grupo",
            ]
        ],
        on="derechohabiencia",
        how="left",
    )

    cubo["derechohabiencia"] = cubo["derechohabiencia"].astype(str)
    cubo["resultado_prueba"] = cubo["resultado_prueba"].astype(str)
    cubo["estatus_paciente"] = cubo["estatus_paciente"].astype(str)
    cubo["total_casos"] = cubo["total_casos"].astype("int64")

    return cubo[
        [
            "derechohabiencia",
            "resultado_prueba",
            "estatus_paciente",
            "total_casos",
            "porcentaje_del_total",
            "tasa_positividad_grupo",
            "tasa_hospitalizacion_grupo",
            "tasa_letalidad_grupo",
        ]
    ]
