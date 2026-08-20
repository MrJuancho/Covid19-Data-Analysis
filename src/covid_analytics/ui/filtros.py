"""Lógica pura de filtrado del tablero (sin dependencia de `streamlit`, FR-004..FR-007)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

import pandas as pd

from covid_analytics.analytics._shared import tasa_segura

Sexo = Literal["M", "F"]
GrupoEdadUi = Literal["<18", "18-39", "40-59", "60+"]
Derechohabiencia = Literal["IMSS", "ISSSTE", "ISSEMYM", "INSABI", "PRIVADO", "NINGUNA"]


@dataclass(frozen=True)
class FiltroTablero:
    """Estado efímero de sesión (nunca persistido a disco)."""

    fecha_inicio: date
    fecha_fin: date
    sexos: tuple[Sexo, ...] = field(default_factory=tuple)
    grupos_edad_ui: tuple[GrupoEdadUi, ...] = field(default_factory=tuple)
    derechohabiencias: tuple[Derechohabiencia, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class VistaKPI:
    """Resultado puro de aplicar `FiltroTablero` sobre los KPIs/series Gold."""

    total_pruebas: int
    casos_positivos_confirmados: int
    tasa_global_positividad: float
    tasa_hospitalizacion: float


def aplicar_filtro_series(df: pd.DataFrame, filtro: FiltroTablero) -> pd.DataFrame:
    """Recorta `series_temporales` al rango `[fecha_inicio, fecha_fin]` inclusive (FR-008)."""
    mascara = (df["fecha"].dt.date >= filtro.fecha_inicio) & (
        df["fecha"].dt.date <= filtro.fecha_fin
    )
    resultado: pd.DataFrame = df.loc[mascara].reset_index(drop=True)
    return resultado


def aplicar_filtro_demografia(df: pd.DataFrame, filtro: FiltroTablero) -> pd.DataFrame:
    """Filtra `metricas_demografia` por sexo y grupo etario UI, con coincidencia
    exacta (FR-004, FR-009; ver Clarifications en spec.md): lista vacía ⟹ sin
    filtrar esa dimensión (incluye `OTRO`/`INDETERMINADO`/`SIN_DATO`); lista no
    vacía ⟹ solo esos valores.
    """
    resultado = df
    if filtro.sexos:
        resultado = resultado[resultado["sexo"].isin(filtro.sexos)]
    if filtro.grupos_edad_ui:
        resultado = resultado[resultado["grupo_edad_ui"].isin(filtro.grupos_edad_ui)]
    return resultado.reset_index(drop=True)


def aplicar_filtro_derechohabiencia(df: pd.DataFrame, filtro: FiltroTablero) -> pd.DataFrame:
    """Filtra `metricas_derechohabiencia` por derechohabiencia, con
    coincidencia exacta (FR-006, misma semántica que `aplicar_filtro_demografia`):
    lista vacía ⟹ sin filtrar (incluye `OTRA`); lista no vacía ⟹ solo esos valores.
    """
    if not filtro.derechohabiencias:
        return df
    resultado: pd.DataFrame = df[df["derechohabiencia"].isin(filtro.derechohabiencias)]
    return resultado.reset_index(drop=True)


def _vista_kpi_desde_cubo(df: pd.DataFrame) -> VistaKPI:
    """Recalcula la vista KPI a partir de un cubo Gold con columnas
    `resultado_prueba`/`estatus_paciente`/`total_casos` (`metricas_demografia`
    o `metricas_derechohabiencia`)."""
    if df.empty:
        return VistaKPI(0, 0, 0.0, 0.0)

    es_positivo = df["resultado_prueba"] == "POSITIVO"
    es_negativo = df["resultado_prueba"] == "NEGATIVO"
    es_hospitalizado = df["estatus_paciente"] == "HOSPITALIZADO"

    positivos = int(df.loc[es_positivo, "total_casos"].sum())
    negativos = int(df.loc[es_negativo, "total_casos"].sum())
    total_pruebas = int(df["total_casos"].sum())
    hospitalizados_positivos = int(df.loc[es_positivo & es_hospitalizado, "total_casos"].sum())

    return VistaKPI(
        total_pruebas=total_pruebas,
        casos_positivos_confirmados=positivos,
        tasa_global_positividad=tasa_segura(positivos, positivos + negativos),
        tasa_hospitalizacion=tasa_segura(hospitalizados_positivos, positivos),
    )


def calcular_vista_kpi(
    kpis_df: pd.DataFrame,
    series_filtrada: pd.DataFrame,
    *,
    sin_filtrar: bool,
    demografia_filtrada: pd.DataFrame | None = None,
    derechohabiencia_filtrada: pd.DataFrame | None = None,
) -> VistaKPI:
    """Calcula las 4 tarjetas KPI (FR-007).

    Prioridad de fuente:
    1. `sin_filtrar=True` -> valores tal cual de `kpis_generales.parquet` (fuente
       autoritativa exacta, sin recomputar).
    2. `derechohabiencia_filtrada` no `None` -> hay un filtro de derechohabiencia
       activo; se recalcula desde ese cubo (misma limitación que el punto 3: el
       filtro de fecha/sexo/edad se ignora, `metricas_derechohabiencia` no tiene
       esas dimensiones). Tiene prioridad sobre `demografia_filtrada` si ambos
       filtros estuvieran activos a la vez.
    3. `demografia_filtrada` no `None` -> hay un filtro de sexo y/o grupo etario
       activo (dimensiones que `series_temporales` no tiene); se recalcula desde
       el cubo demográfico ya filtrado. El filtro de fecha se ignora en este caso
       (`metricas_demografia` no tiene dimensión de fecha) — limitación conocida
       y documentada de agregar sobre tablas Gold de una sola dimensión cada una.
    4. En otro caso -> se recalcula desde `series_filtrada` (solo filtro de
       fecha activo), con `tasa_hospitalizacion` aproximada porque
       `ingresos_hospitalarios` no está desglosado por resultado de prueba en
       la serie diaria.
    """
    if sin_filtrar and not kpis_df.empty:
        fila = kpis_df.iloc[0]
        return VistaKPI(
            total_pruebas=int(fila["total_pacientes_atendidos"]),
            casos_positivos_confirmados=int(fila["total_positivos"]),
            tasa_global_positividad=float(fila["tasa_global_positividad"]),
            tasa_hospitalizacion=float(fila["tasa_global_hospitalizacion"]),
        )

    if derechohabiencia_filtrada is not None:
        return _vista_kpi_desde_cubo(derechohabiencia_filtrada)

    if demografia_filtrada is not None:
        return _vista_kpi_desde_cubo(demografia_filtrada)

    if series_filtrada.empty:
        return VistaKPI(0, 0, 0.0, 0.0)

    positivos = int(series_filtrada["resultados_positivos"].sum())
    negativos = int(series_filtrada["resultados_negativos"].sum())
    pruebas = int(series_filtrada["pruebas_tomadas"].sum())
    hospitalizados = int(series_filtrada["ingresos_hospitalarios"].sum())
    return VistaKPI(
        total_pruebas=pruebas,
        casos_positivos_confirmados=positivos,
        tasa_global_positividad=tasa_segura(positivos, positivos + negativos),
        tasa_hospitalizacion=tasa_segura(hospitalizados, positivos),
    )
