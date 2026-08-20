"""Parser de fechas polimórfico y corrector de columnas intercambiadas (FR-005)."""

from __future__ import annotations

import re
from datetime import date, datetime

import pandas as pd

_PATRON_FECHA_DDMMYYYY = re.compile(r"(\d{1,2}/\d{1,2}/\d{2,4})")
_PATRON_FECHA_YYYYMMDD = re.compile(r"(\d{4}-\d{1,2}-\d{1,2})")

# Ventana epidemiológica válida del dataset (Hospital Gustavo Baz, vigilancia
# COVID-19). Cualquier fecha que parsee estructuralmente pero caiga fuera de
# este rango se trata como un typo de captura y se descarta como NaT/None,
# evitando que un año corrupto (ej. "0202" en vez de "2020") infle el índice
# temporal continuo de la capa Gold (`analytics/series_tiempo.py`).
FECHA_MIN_VALIDA = date(2020, 1, 1)
FECHA_MAX_VALIDA = date(2023, 12, 31)

# Typos de año conocidos observados en la captura manual del dataset. Se
# corrigen sobre el texto crudo, antes de aplicar los patrones regex de
# extracción de fecha, para que el parseo posterior recupere la fecha real
# en vez de descartarla o interpretarla con un año arbitrario.
_TYPOS_ANIO_A_CORREGIR: dict[str, str] = {
    "0202": "2020",
    "2920": "2020",
}

# Corrección específica de este dataset: el archivo fuente
# (RED-NEGATIVA-COVID-02_VIGILANCIA-HOSPITALARIA) se capturó/gestionó
# únicamente hasta enero de 2022. Cualquier fecha con año 2022 en meses
# *posteriores* a enero es un typo de captura del año real 2020 (mismo
# mes/día) -- confirmado por una concentración atípica de +300 registros
# reales en sep-oct/2022 sin un solo registro en enero/2022. Se corrige tras
# el parseo (por año numérico, no como substring de texto) para cubrir
# también datetimes nativos y seriales de Excel, no solo strings.
_ANIO_TYPO_DATASET = 2022
_ANIO_TYPO_DATASET_CORREGIDO = 2020
_MES_LIMITE_GESTION_DATASET = 1  # enero: último mes de captura genuina


def normalizar_typo_anio(texto: str) -> str:
    """Corrige errores de digitación conocidos en el año dentro de fechas en
    texto (ej. `'0202'` o `'2920'` en vez de `'2020'`) antes del parseo."""
    resultado = texto
    for typo, correccion in _TYPOS_ANIO_A_CORREGIR.items():
        resultado = resultado.replace(typo, correccion)
    return resultado


def _corregir_anio_typo_dataset(fecha: datetime) -> datetime:
    if fecha.year == _ANIO_TYPO_DATASET and fecha.month > _MES_LIMITE_GESTION_DATASET:
        return fecha.replace(year=_ANIO_TYPO_DATASET_CORREGIDO)
    return fecha


def _dentro_de_ventana_epidemiologica(fecha: datetime) -> bool:
    return FECHA_MIN_VALIDA <= fecha.date() <= FECHA_MAX_VALIDA


def _parse_sin_validar_ventana(valor: object) -> datetime | None:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, pd.Timestamp):
        return valor.to_pydatetime()
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int | float):
        if pd.isna(valor):
            return None
        origen = pd.Timestamp("1899-12-30")
        return (origen + pd.to_timedelta(float(valor), unit="D")).to_pydatetime()
    if isinstance(valor, str):
        texto = normalizar_typo_anio(valor.strip())
        match = _PATRON_FECHA_DDMMYYYY.search(texto) or _PATRON_FECHA_YYYYMMDD.search(texto)
        candidato = match.group(1) if match else texto
        parsed = pd.to_datetime(candidato, dayfirst=True, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.to_pydatetime()
    return None


def _parse_fecha_polimorfica_interno(valor: object) -> tuple[datetime | None, bool]:
    """Retorna `(fecha_o_none, fue_anomalia_fuera_de_ventana)`.

    `fue_anomalia_fuera_de_ventana` es `True` únicamente cuando el valor
    parseó estructuralmente pero cayó fuera de `[FECHA_MIN_VALIDA,
    FECHA_MAX_VALIDA]` (typo de año) -- se distingue de un dato genuinamente
    ausente o no-fecha (`False`), para poder telemetrar la anomalía sin
    confundirla con la ausencia normal de dato.
    """
    parsed = _parse_sin_validar_ventana(valor)
    if parsed is None:
        return None, False
    parsed = _corregir_anio_typo_dataset(parsed)
    if not _dentro_de_ventana_epidemiologica(parsed):
        return None, True
    return parsed, False


def parse_fecha_polimorfica(valor: object) -> datetime | None:
    """Reconoce datetime nativo, serial de Excel, strings estructurados/con
    ruido, y retorna `None` (NaT) para valores clínicos no-fecha (research.md
    #3) o para fechas fuera de la ventana epidemiológica válida (typos de
    año)."""
    fecha, _ = _parse_fecha_polimorfica_interno(valor)
    return fecha


def parse_fecha_con_telemetria(valor: object) -> tuple[datetime | None, bool]:
    """Como `parse_fecha_polimorfica`, pero además indica si el valor se
    descartó específicamente por caer fuera de la ventana epidemiológica
    (anomalía de typo de año), para alimentar el conteo de
    `fechas_anomalas_fuera_ventana` en `data_quality_summary.json`."""
    return _parse_fecha_polimorfica_interno(valor)


def corregir_resultado_fecha_intercambiados(
    resultado_raw: str | None, fecha_resultado_raw: object
) -> tuple[str | None, object]:
    """Si `resultado_raw` en realidad contiene una fecha y `fecha_resultado_raw`
    contiene texto categórico, intercambia los valores a sus columnas lógicas
    (spec.md, User Story 2, Acceptance Scenario 3)."""
    if resultado_raw is None or not isinstance(fecha_resultado_raw, str):
        return resultado_raw, fecha_resultado_raw

    resultado_es_fecha = parse_fecha_polimorfica(resultado_raw) is not None
    fecha_resultado_es_texto = parse_fecha_polimorfica(fecha_resultado_raw) is None
    if resultado_es_fecha and fecha_resultado_es_texto:
        nuevo_resultado: str | None = fecha_resultado_raw
        nueva_fecha_resultado: object = resultado_raw
        return nuevo_resultado, nueva_fecha_resultado
    return resultado_raw, fecha_resultado_raw
