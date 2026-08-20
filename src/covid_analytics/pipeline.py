"""CLI del pipeline ETL de COVID-19 (contracts/pipeline_cli.md)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Literal

import pandas as pd

from covid_analytics.analytics import generar_capa_gold
from covid_analytics.cleaning import limpiar_silver
from covid_analytics.ingestion import ingerir_bronze
from covid_analytics.models import CasoUnificadoSilver, construir_resumen_calidad

logger = logging.getLogger("covid_analytics.pipeline")

NOMBRE_ARCHIVO_PARQUET = "casos_unificados.parquet"
NOMBRE_ARCHIVO_RESUMEN = "data_quality_summary.json"


_COLUMNAS_FECHA_SILVER = [
    "fecha_notificacion",
    "fecha_toma_muestra",
    "fecha_resultado",
    "fecha_ingreso_hospital",
]


def _construir_dataframe_silver(casos: list[CasoUnificadoSilver]) -> pd.DataFrame:
    registros = [caso.model_dump() for caso in casos]
    df = pd.DataFrame.from_records(registros, columns=list(CasoUnificadoSilver.model_fields.keys()))
    for columna in _COLUMNAS_FECHA_SILVER:
        df[columna] = pd.to_datetime(df[columna])
    return df


def _escribir_parquet(df: pd.DataFrame, destino: Path) -> None:
    df.to_parquet(destino, engine="pyarrow", compression="snappy", index=False)


def ejecutar_pipeline(
    excel_path: str | Path,
    output_dir: str | Path,
    salt: str | None = None,
    *,
    layer: Literal["silver", "gold"] = "silver",
    gold_output_dir: str | Path = "data/gold",
) -> None:
    """Orquesta ingestión Bronze -> limpieza/cruce Silver -> (opcional) Gold.

    Con `layer="gold"`, además de la capa Silver genera la capa Gold
    (`covid_analytics.analytics.generar_capa_gold`) a partir del mismo
    DataFrame Silver ya calculado en memoria, sin releer el Parquet.

    Nunca registra valores de columnas PII en logs (Principio I, SC-001).
    """
    destino_dir = Path(output_dir)
    destino_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Iniciando ingesta Bronze desde '%s'", Path(excel_path).name)
    resultado_ingesta = ingerir_bronze(excel_path, salt=salt)
    logger.info(
        "Ingesta Bronze completa: %d filas Seguimiento, %d filas Nominal, %d registros hasheados",
        resultado_ingesta.filas_leidas_seguimiento,
        resultado_ingesta.filas_leidas_nominal,
        len(resultado_ingesta.casos),
    )

    resultado_limpieza = limpiar_silver(resultado_ingesta.casos)
    logger.info(
        "Limpieza Silver completa: %d cruces exitosos, %d huerfanos, %d correcciones, "
        "%d colisiones, %d fechas anomalas fuera de ventana",
        resultado_limpieza.cruces_exitosos,
        resultado_limpieza.registros_huerfanos,
        resultado_limpieza.correcciones_columnas_intercambiadas,
        resultado_limpieza.colisiones_llave_sintetica,
        resultado_limpieza.fechas_anomalas_fuera_ventana,
    )

    df_silver = _construir_dataframe_silver(resultado_limpieza.casos)
    _escribir_parquet(df_silver, destino_dir / NOMBRE_ARCHIVO_PARQUET)

    if layer == "gold":
        logger.info("Iniciando generación de la capa Gold")
        generar_capa_gold(df_silver, gold_output_dir)
        logger.info("Capa Gold completa en '%s'", gold_output_dir)

    resumen = construir_resumen_calidad(
        filas_leidas_bronze_seguimiento=resultado_ingesta.filas_leidas_seguimiento,
        filas_leidas_bronze_nominal=resultado_ingesta.filas_leidas_nominal,
        registros_hasheados=len(resultado_ingesta.casos),
        cruces_exitosos=resultado_limpieza.cruces_exitosos,
        registros_huerfanos=resultado_limpieza.registros_huerfanos,
        correcciones_columnas_intercambiadas=resultado_limpieza.correcciones_columnas_intercambiadas,
        colisiones_llave_sintetica=resultado_limpieza.colisiones_llave_sintetica,
        fechas_anomalas_fuera_ventana=resultado_limpieza.fechas_anomalas_fuera_ventana,
    )
    (destino_dir / NOMBRE_ARCHIVO_RESUMEN).write_text(
        json.dumps(resumen.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Pipeline finalizado; salida escrita en '%s'", destino_dir)


def _parsear_argumentos(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="covid-analytics", description="Pipeline ETL de COVID-19 (Bronze a Silver)"
    )
    parser.add_argument("--excel-path", required=True, help="Ruta al .xlsx de origen")
    parser.add_argument(
        "--output-dir", default="data/silver", help="Carpeta destino (default: data/silver)"
    )
    parser.add_argument(
        "--layer",
        choices=["silver", "gold"],
        default="silver",
        help="Capa objetivo del pipeline: 'silver' (default) o 'gold' (Bronze -> Silver -> Gold)",
    )
    parser.add_argument(
        "--gold-output-dir",
        default="data/gold",
        help="Carpeta destino de la capa Gold cuando --layer=gold (default: data/gold)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _parsear_argumentos(argv)
    try:
        ejecutar_pipeline(
            args.excel_path,
            args.output_dir,
            layer=args.layer,
            gold_output_dir=args.gold_output_dir,
        )
    except Exception as exc:  # noqa: BLE001 - frontera del CLI: reportar sin filtrar PII
        print(f"Error ejecutando el pipeline: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
