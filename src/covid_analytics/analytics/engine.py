"""Orquestador, validación de contrato de entrada, consistencia marginal, CLI
y persistencia de la capa Gold (FR-001, FR-003, FR-006, FR-007, US4)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from covid_analytics.analytics._shared import GoldIntegrityError, tasa_segura
from covid_analytics.analytics.demografia import calcular_metricas_demografia
from covid_analytics.analytics.derechohabiencia import calcular_metricas_derechohabiencia
from covid_analytics.analytics.geografia import calcular_distribucion_geografica
from covid_analytics.analytics.series_tiempo import calcular_series_temporales
from covid_analytics.cleaning.fechas import FECHA_MAX_VALIDA, FECHA_MIN_VALIDA
from covid_analytics.models import CasoUnificadoSilver, KpisGeneralesGold

logger = logging.getLogger("covid_analytics.analytics.engine")

_NOMBRE_METRICAS_DEMOGRAFIA = "metricas_demografia.parquet"
_NOMBRE_SERIES_TEMPORALES = "series_temporales.parquet"
_NOMBRE_DISTRIBUCION_GEOGRAFICA = "distribucion_geografica.parquet"
_NOMBRE_KPIS_GENERALES = "kpis_generales.parquet"
_NOMBRE_METRICAS_DERECHOHABIENCIA = "metricas_derechohabiencia.parquet"
_NOMBRE_RESUMEN_EJECUTIVO = "resumen_ejecutivo.json"


def _validar_contrato_silver(df: pd.DataFrame) -> None:
    """Valida conformidad estructural con `CasoUnificadoSilver` (FR-001)."""
    columnas_requeridas = set(CasoUnificadoSilver.model_fields.keys())
    faltantes = columnas_requeridas - set(df.columns)
    if faltantes:
        raise ValueError(f"Columnas faltantes respecto al contrato Silver: {sorted(faltantes)}")


def cargar_silver(silver_path: str | Path) -> pd.DataFrame:
    """Carga y valida `data/silver/casos_unificados.parquet` (FR-001)."""
    ruta = Path(silver_path)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo Silver: {ruta}")
    df = pd.read_parquet(ruta)
    _validar_contrato_silver(df)
    return df


def calcular_kpis_generales(
    df_silver: pd.DataFrame, *, casos_fechas_invertidas: int
) -> KpisGeneralesGold:
    """Sintetiza los KPIs macro/globales de la capa Gold (FR-003, US4)."""
    resultado = df_silver["resultado_prueba"]
    estatus = df_silver["estatus_paciente"]

    total_positivos = int((resultado == "POSITIVO").sum())
    total_negativos = int((resultado == "NEGATIVO").sum())
    defunciones_positivas = int(((resultado == "POSITIVO") & (estatus == "DEFUNCION")).sum())
    hospitalizados_positivos = int(((resultado == "POSITIVO") & (estatus == "HOSPITALIZADO")).sum())

    lags = df_silver.loc[
        df_silver["es_registro_unificado"].astype(bool), "dias_entre_notificacion_e_ingreso"
    ].dropna()
    mediana_lag = float(lags.median()) if not lags.empty else None

    return KpisGeneralesGold(
        total_pacientes_atendidos=len(df_silver),
        total_positivos=total_positivos,
        total_negativos=total_negativos,
        total_pendientes=int((resultado == "PENDIENTE").sum()),
        total_no_concluyentes=int((resultado == "NO_CONCLUYENTE").sum()),
        total_hospitalizados=int((estatus == "HOSPITALIZADO").sum()),
        total_defunciones=int((estatus == "DEFUNCION").sum()),
        tasa_global_positividad=tasa_segura(total_positivos, total_positivos + total_negativos),
        tasa_global_letalidad=tasa_segura(defunciones_positivas, total_positivos),
        tasa_global_hospitalizacion=tasa_segura(hospitalizados_positivos, total_positivos),
        registros_unificados_cruce=int(df_silver["es_registro_unificado"].astype(bool).sum()),
        mediana_dias_notificacion_ingreso=mediana_lag,
        casos_fechas_invertidas=casos_fechas_invertidas,
        timestamp_generacion=datetime.now(UTC).isoformat(),
    )


def verificar_consistencia_marginal(
    df_silver: pd.DataFrame,
    demografia: pd.DataFrame,
    series: pd.DataFrame,
    geografia: pd.DataFrame,
    kpis: KpisGeneralesGold,
    derechohabiencia: pd.DataFrame,
) -> None:
    """Verifica coincidencia aritmética exacta entre las tablas Gold y Silver
    (FR-007, SC-002). Lanza `GoldIntegrityError` ante cualquier discrepancia."""
    total_filas = len(df_silver)
    total_positivos_silver = int((df_silver["resultado_prueba"] == "POSITIVO").sum())
    # series_temporales solo cuenta filas con fecha_resultado no nula y dentro
    # de la ventana epidemiológica (FR-004 Acceptance Scenario 2: los casos
    # sin fecha válida se aíslan sin romper la continuidad del índice, en vez
    # de forzarlos a un día arbitrario -- ver también el acotado defensivo en
    # `series_tiempo.py`). Por eso su "fila válida" para positividad es un
    # subconjunto del total Silver.
    fecha_resultado_en_ventana = df_silver["fecha_resultado"].notna() & (
        df_silver["fecha_resultado"].between(
            pd.Timestamp(FECHA_MIN_VALIDA), pd.Timestamp(FECHA_MAX_VALIDA)
        )
    )
    total_positivos_con_fecha_resultado = int(
        ((df_silver["resultado_prueba"] == "POSITIVO") & fecha_resultado_en_ventana).sum()
    )

    conteos_filas = {
        "metricas_demografia.total_casos": int(demografia["total_casos"].sum()),
        "distribucion_geografica.total_casos": int(geografia["total_casos"].sum()),
        "kpis_generales.total_pacientes_atendidos": kpis.total_pacientes_atendidos,
        "metricas_derechohabiencia.total_casos": int(derechohabiencia["total_casos"].sum()),
    }
    for nombre, valor in conteos_filas.items():
        if valor != total_filas:
            raise GoldIntegrityError(
                f"Inconsistencia de filas: {nombre}={valor}, esperado {total_filas} (Silver)"
            )

    # FR-005a: grupo_edad y grupo_edad_ui se calculan independientemente desde
    # `edad`, pero ambas DEBEN coincidir en qué filas son SIN_DATO (mismo
    # sentinel de origen) -- ver data-model.md, "Regla de integridad añadida".
    filas_sin_dato_canonico = int(
        demografia.loc[demografia["grupo_edad"] == "SIN_DATO", "total_casos"].sum()
    )
    filas_sin_dato_ui = int(
        demografia.loc[demografia["grupo_edad_ui"] == "SIN_DATO", "total_casos"].sum()
    )
    if filas_sin_dato_canonico != filas_sin_dato_ui:
        raise GoldIntegrityError(
            "Inconsistencia grupo_edad_ui: filas SIN_DATO en grupo_edad="
            f"{filas_sin_dato_canonico}, en grupo_edad_ui={filas_sin_dato_ui}"
        )

    conteos_positivos = {
        "metricas_demografia.positivos": (
            int(demografia.loc[demografia["resultado_prueba"] == "POSITIVO", "total_casos"].sum()),
            total_positivos_silver,
        ),
        "distribucion_geografica.total_positivos": (
            int(geografia["total_positivos"].sum()),
            total_positivos_silver,
        ),
        "kpis_generales.total_positivos": (kpis.total_positivos, total_positivos_silver),
        "series_temporales.resultados_positivos": (
            int(series["resultados_positivos"].sum()),
            total_positivos_con_fecha_resultado,
        ),
        "metricas_derechohabiencia.positivos": (
            int(
                derechohabiencia.loc[
                    derechohabiencia["resultado_prueba"] == "POSITIVO", "total_casos"
                ].sum()
            ),
            total_positivos_silver,
        ),
    }
    for nombre, (valor, esperado) in conteos_positivos.items():
        if valor != esperado:
            raise GoldIntegrityError(
                f"Inconsistencia de positivos: {nombre}={valor}, esperado {esperado}"
            )


def _persistir_parquet(tabla: pd.DataFrame, destino: Path) -> None:
    tabla.to_parquet(destino, engine="pyarrow", compression="snappy", index=False)


def generar_capa_gold(df_silver: pd.DataFrame, output_dir: str | Path) -> None:
    """Orquesta la generación completa de la capa Gold (FR-006, US4).

    Calcula las cuatro tablas analíticas y el resumen ejecutivo, verifica la
    consistencia marginal (FR-007) y persiste todo en `output_dir`.
    """
    destino = Path(output_dir)
    destino.mkdir(parents=True, exist_ok=True)

    demografia_df = calcular_metricas_demografia(df_silver)
    series_df, casos_fechas_invertidas = calcular_series_temporales(df_silver)
    geografia_df = calcular_distribucion_geografica(df_silver)
    derechohabiencia_df = calcular_metricas_derechohabiencia(df_silver)
    kpis = calcular_kpis_generales(df_silver, casos_fechas_invertidas=casos_fechas_invertidas)

    verificar_consistencia_marginal(
        df_silver, demografia_df, series_df, geografia_df, kpis, derechohabiencia_df
    )

    _persistir_parquet(demografia_df, destino / _NOMBRE_METRICAS_DEMOGRAFIA)
    _persistir_parquet(series_df, destino / _NOMBRE_SERIES_TEMPORALES)
    _persistir_parquet(geografia_df, destino / _NOMBRE_DISTRIBUCION_GEOGRAFICA)
    _persistir_parquet(derechohabiencia_df, destino / _NOMBRE_METRICAS_DERECHOHABIENCIA)
    _persistir_parquet(pd.DataFrame([kpis.model_dump()]), destino / _NOMBRE_KPIS_GENERALES)
    (destino / _NOMBRE_RESUMEN_EJECUTIVO).write_text(
        json.dumps(kpis.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Capa Gold generada en '%s'", destino)


def _parsear_argumentos(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="covid-analytics-gold",
        description="Generación de la capa Gold de analítica epidemiológica",
    )
    parser.add_argument(
        "--silver-path",
        default="data/silver/casos_unificados.parquet",
        help="Ruta al Parquet de la capa Silver (default: data/silver/casos_unificados.parquet)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/gold",
        help="Carpeta destino de la capa Gold (default: data/gold)",
    )
    parser.add_argument("--verbose", action="store_true", help="Activa logs de depuración")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parsear_argumentos(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        df_silver = cargar_silver(args.silver_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error de lectura de la capa Silver: {exc}", file=sys.stderr)
        return 1

    try:
        generar_capa_gold(df_silver, args.output_dir)
    except GoldIntegrityError as exc:
        print(f"Error de integridad estadistica en la capa Gold: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
