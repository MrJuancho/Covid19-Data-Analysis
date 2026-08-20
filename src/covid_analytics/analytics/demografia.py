"""Agregaciones demográficas y de positividad multidimensional (FR-002, FR-003, US1)."""

from __future__ import annotations

import pandas as pd

from covid_analytics.analytics._shared import tasa_segura

GRUPOS_EDAD_CANONICOS: list[str] = [
    "0-1",
    "2-11",
    "12-17",
    "18-24",
    "25-30",
    "31-35",
    "36-40",
    "41-45",
    "46-50",
    "51-55",
    "56-60",
    "61-65",
    "66+",
    "SIN_DATO",
]

_BIN_EDGES = [
    0.0,
    1.0,
    11.0,
    17.0,
    24.0,
    30.0,
    35.0,
    40.0,
    45.0,
    50.0,
    55.0,
    60.0,
    65.0,
    float("inf"),
]
_BIN_LABELS = GRUPOS_EDAD_CANONICOS[:-1]

GRUPOS_EDAD_UI_CANONICOS: list[str] = ["<18", "18-39", "40-59", "60+", "SIN_DATO"]

# FR-005a: cortes exactos en 18/40/60 años, independientes de `GRUPOS_EDAD_CANONICOS`
# (cuyos bins "36-40" y "56-60" cruzan esos cortes y producirían clasificación
# incorrecta si se derivaran por redondeo -- ver spec.md, sesión de /speckit-clarify).
_BIN_EDGES_UI = [0.0, 18.0, 40.0, 60.0, float("inf")]
_BIN_LABELS_UI = GRUPOS_EDAD_UI_CANONICOS[:-1]


def _asignar_bins(
    edad: pd.Series, bins: list[float], labels: list[str], categorias: list[str], *, right: bool
) -> pd.Categorical[str]:
    sin_dato = edad.isna() | (edad < 0.0)
    grupos = pd.cut(
        edad.mask(sin_dato),
        bins=bins,
        labels=labels,
        right=right,
        include_lowest=True,
    ).astype("string")
    grupos = grupos.mask(sin_dato, "SIN_DATO")
    return pd.Categorical(grupos, categories=categorias)


def asignar_grupo_edad(edad: pd.Series) -> pd.Categorical[str]:
    """Clasifica `edad` en los 14 grupos etarios canónicos (FR-002), ej. `"0-1"`
    cubre las edades 0 y 1 inclusive (bins cerrados por la derecha).

    El sentinel `-1.0` (o nulo) de la capa Silver se asigna a `SIN_DATO`.
    """
    return _asignar_bins(edad, _BIN_EDGES, _BIN_LABELS, GRUPOS_EDAD_CANONICOS, right=True)


def asignar_grupo_edad_ui(edad: pd.Series) -> pd.Categorical[str]:
    """Clasifica `edad` en los 4 buckets de UI (`<18`/`18-39`/`40-59`/`60+`) con
    cortes exactos semiabiertos `[0,18)`, `[18,40)`, `[40,60)`, `[60,inf)`
    (FR-005a). El sentinel `-1.0` (o nulo) se asigna a `SIN_DATO`, igual que
    `asignar_grupo_edad`.
    """
    return _asignar_bins(edad, _BIN_EDGES_UI, _BIN_LABELS_UI, GRUPOS_EDAD_UI_CANONICOS, right=False)


def calcular_metricas_demografia(df_silver: pd.DataFrame) -> pd.DataFrame:
    """Cubo (grupo_edad x grupo_edad_ui x sexo x resultado_prueba x
    estatus_paciente) con conteos, participación porcentual y tasa de
    positividad por grupo demográfico (grupo_edad x sexo) (FR-002, FR-003,
    FR-005a).

    `grupo_edad_ui` se asigna directamente desde `edad` con cortes exactos
    (no derivada de `grupo_edad`) y se mantiene como columna no-categórica en
    el groupby para evitar una expansión cruzada artificial con los 14 bins
    canónicos de `grupo_edad` (que sí preserva su rango completo, incluyendo
    bins vacíos, vía `observed=False`).
    """
    df = df_silver.copy()
    df["grupo_edad"] = asignar_grupo_edad(df["edad"])
    df["grupo_edad_ui"] = asignar_grupo_edad_ui(df["edad"])
    df["grupo_edad_ui"] = df["grupo_edad_ui"].astype(str)
    df["es_positivo"] = df["resultado_prueba"] == "POSITIVO"
    df["es_negativo"] = df["resultado_prueba"] == "NEGATIVO"

    cubo = (
        df.groupby(
            ["grupo_edad", "grupo_edad_ui", "sexo", "resultado_prueba", "estatus_paciente"],
            observed=False,
        )
        .size()
        .rename("total_casos")
        .reset_index()
    )

    total_global = len(df_silver)
    cubo["porcentaje_del_total"] = cubo["total_casos"] / total_global if total_global > 0 else 0.0

    positividad_grupo = (
        df.groupby(["grupo_edad", "sexo"], observed=False)
        .agg(positivos=("es_positivo", "sum"), negativos=("es_negativo", "sum"))
        .reset_index()
    )
    positividad_grupo["tasa_positividad_grupo"] = positividad_grupo.apply(
        lambda fila: tasa_segura(fila["positivos"], fila["positivos"] + fila["negativos"]), axis=1
    )

    cubo = cubo.merge(
        positividad_grupo[["grupo_edad", "sexo", "tasa_positividad_grupo"]],
        on=["grupo_edad", "sexo"],
        how="left",
    )

    cubo["grupo_edad"] = cubo["grupo_edad"].astype(str)
    cubo["sexo"] = cubo["sexo"].astype(str)
    cubo["resultado_prueba"] = cubo["resultado_prueba"].astype(str)
    cubo["estatus_paciente"] = cubo["estatus_paciente"].astype(str)
    cubo["total_casos"] = cubo["total_casos"].astype("int64")

    return cubo
