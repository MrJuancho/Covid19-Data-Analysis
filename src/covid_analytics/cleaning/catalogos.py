"""Catálogos canónicos cerrados: municipio (FR-006), resultado_prueba y
estatus_paciente (FR-009)."""

from __future__ import annotations

import unicodedata

from covid_analytics.models import EstatusPaciente, ResultadoPrueba

_MUNICIPIO_OTROS = "OTROS"

# FR-006: catálogo explícito de equivalencias (mapeo directo de nombres),
# no filtros regex amplios. Claves ya normalizadas (mayúsculas, sin acentos).
_CATALOGO_MUNICIPIO: dict[str, str] = {
    "GAM": "GUSTAVO A. MADERO",
    "GUSTAVO A MADERO": "GUSTAVO A. MADERO",
    "GUSTAVO A. MADERO": "GUSTAVO A. MADERO",
    "IZTAPALAPA": "IZTAPALAPA",
    "IZTAP": "IZTAPALAPA",
    "TLALNEPANTLA": "TLALNEPANTLA",
    "TLALNEPANTLA DE BAZ": "TLALNEPANTLA",
    "NAUCALPAN": "NAUCALPAN",
    "NAUCALPAN DE JUAREZ": "NAUCALPAN",
    "ECATEPEC": "ECATEPEC",
    "ECATEPEC DE MORELOS": "ECATEPEC",
    "COYOACAN": "COYOACAN",
    "TLALPAN": "TLALPAN",
    "CUAUHTEMOC": "CUAUHTEMOC",
    "AZCAPOTZALCO": "AZCAPOTZALCO",
    "NEZAHUALCOYOTL": "NEZAHUALCOYOTL",
    "TOLUCA": "TOLUCA",
}

# FR-009: diccionarios canónicos cerrados de resultado_prueba.
_RESULTADO_PRUEBA: dict[ResultadoPrueba, list[str]] = {
    "POSITIVO": ["POSITIVO", "SARS-COV-2", "DETECTADO", "POS", "CONFIRMADO", "+", "REACTIVO"],
    "NEGATIVO": ["NEGATIVO", "NO DETECTADO", "NEG", "-", "NO REACTIVO"],
    "PENDIENTE": [
        "PENDIENTE",
        "PEDIENTE",
        "EN PROCESO",
        "EN ANALISIS",
        "S/R",
        "SIN RESULTADO",
        "TRAMITE",
        "NO SE TOMO",
        "NO SE TOMÓ",
    ],
    "NO_CONCLUYENTE": [
        "INSUFICIENTE",
        "NO CONCLUYENTE",
        "INDETERMINADO",
        "MUESTRA INADECUADA",
        "REPETIR",
        "RECHAZO",
        "RECHAZADA",
    ],
}

# FR-009: diccionarios canónicos cerrados de estatus_paciente.
_ESTATUS_PACIENTE: dict[EstatusPaciente, list[str]] = {
    "AMBULATORIO": ["AMBULATORIO", "DOMICILIO", "CASA", "ALTA", "ESTABLE"],
    "HOSPITALIZADO": [
        "HOSPITALIZADO",
        "HOSPITAL",
        "INTERNADO",
        "UCI",
        "TERAPIA INTENSIVA",
        "URGENCIAS",
    ],
    "DEFUNCION": ["DEFUNCION", "FINADO", "FALLECIDO", "MUERTE", "OBITO", "DECEDIDO"],
}


def _normalizar_texto(texto: str) -> str:
    mayusculas = texto.upper()
    descompuesto = unicodedata.normalize("NFD", mayusculas)
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return " ".join(sin_acentos.split())


def _construir_indice[T: str](catalogo: dict[T, list[str]]) -> dict[str, T]:
    indice: dict[str, T] = {}
    for canonico, sinonimos in catalogo.items():
        for sinonimo in sinonimos:
            indice[_normalizar_texto(sinonimo)] = canonico
    return indice


_INDICE_RESULTADO_PRUEBA = _construir_indice(_RESULTADO_PRUEBA)
_INDICE_ESTATUS_PACIENTE = _construir_indice(_ESTATUS_PACIENTE)
_INDICE_MUNICIPIO = {_normalizar_texto(k): v for k, v in _CATALOGO_MUNICIPIO.items()}


def estandarizar_municipio(valor: str | None) -> str:
    """FR-006: catálogo explícito; residencias no identificadas -> `OTROS`."""
    if valor is None:
        return _MUNICIPIO_OTROS
    return _INDICE_MUNICIPIO.get(_normalizar_texto(valor), _MUNICIPIO_OTROS)


def estandarizar_resultado_prueba(valor: str | None) -> ResultadoPrueba:
    """FR-009: diccionario canónico cerrado; fallback -> `NO_ESPECIFICADO`."""
    if valor is None:
        return "NO_ESPECIFICADO"
    resultado = _INDICE_RESULTADO_PRUEBA.get(_normalizar_texto(valor))
    return resultado if resultado is not None else "NO_ESPECIFICADO"


def estandarizar_estatus_paciente(valor: str | None) -> EstatusPaciente:
    """FR-009: diccionario canónico cerrado; fallback -> `NO_ESPECIFICADO`."""
    if valor is None:
        return "NO_ESPECIFICADO"
    estatus = _INDICE_ESTATUS_PACIENTE.get(_normalizar_texto(valor))
    return estatus if estatus is not None else "NO_ESPECIFICADO"
