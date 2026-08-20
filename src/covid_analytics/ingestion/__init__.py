"""Orquestación de la capa Bronze: lectura acotada + seudonimización de PII."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from covid_analytics.ingestion.excel_reader import leer_hoja_acotada
from covid_analytics.ingestion.pii import generar_hash_pii, obtener_salt
from covid_analytics.models import CasoBronze

HOJA_RED_NEGATIVA = "RED NEGATIVA"
HOJA_SEGUIMIENTO = "SEGUIMIENTO DE CASOS COVID 19"
HOJA_NOMINAL = " NOMINAL DE HOSPITALIZADOS"

_COLUMNAS_CLAVE_RED_NEGATIVA = ["HOSPITAL"]
_COLUMNAS_CLAVE_SEGUIMIENTO = ["NO. (consecutivo)", "CASO"]
_COLUMNAS_CLAVE_NOMINAL = ["HOSPITAL", "NOMBRE DEL PACIENTE"]
_FILAS_ENCABEZADO_NOMINAL = 3


def _valor_o_none(valor: Any) -> Any:
    if valor is None:
        return None
    if isinstance(valor, float) and pd.isna(valor):
        return None
    return valor


def _a_str_o_none(valor: Any) -> str | None:
    valor = _valor_o_none(valor)
    return None if valor is None else str(valor)


def _resolver_columna(nombres_columna: list[str], fragmento: str) -> str | None:
    """Encuentra el nombre real de columna cuyo segmento (parte antes/después
    de ' | ' en encabezados combinados) empieza con `fragmento`, sin distinguir
    mayúsculas. Los encabezados reales siempre inician con el nombre de campo
    seguido de una descripción entre paréntesis (ver docs/audit_legacy.md).

    Si `fragmento` en sí contiene ' | ' (para referirse a una columna
    combinada específica, ej. "EDAD | F"), se compara contra el nombre
    completo en lugar de por segmento individual."""
    frag = fragmento.upper()
    if " | " in frag:
        for nombre in nombres_columna:
            if nombre.upper() == frag or nombre.upper().startswith(frag):
                return nombre
        return None
    for nombre in nombres_columna:
        segmentos = [s.strip().upper() for s in nombre.split(" | ")]
        if any(s.startswith(frag) for s in segmentos):
            return nombre
    return None


class _MapaColumnas:
    """Resuelve nombres lógicos -> nombres reales de columna una sola vez por
    DataFrame, evitando re-buscar por cada fila."""

    def __init__(self, columnas: list[str], especificacion: dict[str, str]) -> None:
        self._mapa = {
            logico: _resolver_columna(columnas, fragmento)
            for logico, fragmento in especificacion.items()
        }

    def valor(self, fila: pd.Series, logico: str) -> Any:
        nombre_real = self._mapa.get(logico)
        if nombre_real is None:
            return None
        return fila.get(nombre_real)


_ESPECIFICACION_SEGUIMIENTO = {
    "folio": "NO.",
    "nombre": "CASO",
    "sexo": "SEXO",
    "edad": "EDAD",
    "municipio": "MUNICIPIO",
    "derechohabiencia": "DERECHOHABIENCIA",
    "fecha_notificacion": "FECHA DE NOTIFIC",
    "fecha_toma_muestra": "FECHA TOMA DE MUESTRA",
    "resultado": "RESULTADO",
    "fecha_resultado": "FECHA DE RESULTADO",
    "estatus": "ESTATUS",
}

_ESPECIFICACION_NOMINAL = {
    "hospital": "HOSPITAL",
    "folio": "NO.",
    "nombre": "NOMBRE DEL PACIENTE",
    "edad_f": "EDAD | F",
    "edad_m": "EDAD | M",
    "fecha_ingreso": "FECHA DE INGRESO",
    "resultado": "RESULTADO",
    "fecha_resultado": "FECHA DE RESULTADO",
}


@dataclass(frozen=True)
class ResultadoIngesta:
    casos: list[CasoBronze]
    filas_leidas_seguimiento: int
    filas_leidas_nominal: int
    filas_leidas_red_negativa: int


def _fila_seguimiento_a_caso(fila: pd.Series, mapa: _MapaColumnas, salt: str) -> CasoBronze:
    nombre = str(_valor_o_none(mapa.valor(fila, "nombre")) or "")
    folio = _valor_o_none(mapa.valor(fila, "folio"))
    return CasoBronze(
        paciente_id=generar_hash_pii(nombre, folio, salt),
        fuente="seguimiento",
        folio_origen=None if folio is None else str(folio),
        sexo_raw=_a_str_o_none(mapa.valor(fila, "sexo")),
        edad_raw=_a_str_o_none(mapa.valor(fila, "edad")),
        municipio_raw=_a_str_o_none(mapa.valor(fila, "municipio")),
        derechohabiencia_raw=_a_str_o_none(mapa.valor(fila, "derechohabiencia")),
        fecha_notificacion_raw=_valor_o_none(mapa.valor(fila, "fecha_notificacion")),
        fecha_toma_muestra_raw=_valor_o_none(mapa.valor(fila, "fecha_toma_muestra")),
        resultado_raw=_a_str_o_none(mapa.valor(fila, "resultado")),
        fecha_resultado_raw=_valor_o_none(mapa.valor(fila, "fecha_resultado")),
        estatus_raw=_a_str_o_none(mapa.valor(fila, "estatus")),
    )


def _fila_nominal_a_caso(fila: pd.Series, mapa: _MapaColumnas, salt: str) -> CasoBronze:
    nombre = str(_valor_o_none(mapa.valor(fila, "nombre")) or "")
    folio = _valor_o_none(mapa.valor(fila, "folio"))
    edad_f = _valor_o_none(mapa.valor(fila, "edad_f"))
    edad_m = _valor_o_none(mapa.valor(fila, "edad_m"))
    if edad_f is not None:
        edad_raw, sexo_raw = edad_f, "F"
    elif edad_m is not None:
        edad_raw, sexo_raw = edad_m, "M"
    else:
        edad_raw, sexo_raw = None, None
    return CasoBronze(
        paciente_id=generar_hash_pii(nombre, folio, salt),
        fuente="nominal",
        folio_origen=None if folio is None else str(folio),
        sexo_raw=sexo_raw,
        edad_raw=None if edad_raw is None else str(edad_raw),
        fecha_toma_muestra_raw=None,
        resultado_raw=_a_str_o_none(mapa.valor(fila, "resultado")),
        fecha_resultado_raw=_valor_o_none(mapa.valor(fila, "fecha_resultado")),
        fecha_ingreso_raw=_valor_o_none(mapa.valor(fila, "fecha_ingreso")),
        hospital_raw=_a_str_o_none(mapa.valor(fila, "hospital")),
    )


def ingerir_bronze(excel_path: str | Path, salt: str | None = None) -> ResultadoIngesta:
    """Lee las 3 hojas auditadas de forma acotada y produce `CasoBronze` con PII
    ya seudonimizada; las columnas PII originales nunca se incluyen en la salida."""
    sal_efectiva = salt if salt is not None else obtener_salt()

    df_red_negativa = leer_hoja_acotada(excel_path, HOJA_RED_NEGATIVA, _COLUMNAS_CLAVE_RED_NEGATIVA)
    df_seguimiento = leer_hoja_acotada(excel_path, HOJA_SEGUIMIENTO, _COLUMNAS_CLAVE_SEGUIMIENTO)
    df_nominal = leer_hoja_acotada(
        excel_path,
        HOJA_NOMINAL,
        _COLUMNAS_CLAVE_NOMINAL,
        filas_encabezado=_FILAS_ENCABEZADO_NOMINAL,
    )

    mapa_seguimiento = _MapaColumnas(list(df_seguimiento.columns), _ESPECIFICACION_SEGUIMIENTO)
    mapa_nominal = _MapaColumnas(list(df_nominal.columns), _ESPECIFICACION_NOMINAL)

    casos: list[CasoBronze] = [
        _fila_seguimiento_a_caso(fila, mapa_seguimiento, sal_efectiva)
        for _, fila in df_seguimiento.iterrows()
    ]
    casos.extend(
        _fila_nominal_a_caso(fila, mapa_nominal, sal_efectiva) for _, fila in df_nominal.iterrows()
    )

    return ResultadoIngesta(
        casos=casos,
        filas_leidas_seguimiento=len(df_seguimiento),
        filas_leidas_nominal=len(df_nominal),
        filas_leidas_red_negativa=len(df_red_negativa),
    )
