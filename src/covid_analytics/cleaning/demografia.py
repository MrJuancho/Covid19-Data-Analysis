"""Unificación demográfica (edad/sexo) y corrector de intercambio sexo↔edad (FR-004)."""

from __future__ import annotations

import re

from covid_analytics.models import Sexo

_PATRON_MESES = re.compile(r"^\d+\s*M$")
_PATRON_DIAS = re.compile(r"^\d+\s*D$")
_PATRON_DIGITOS = re.compile(r"\d+")

_CODIGOS_SEXO = {"F", "M"}


def _es_codigo_sexo(texto: str | None) -> bool:
    return texto is not None and texto.strip().upper() in _CODIGOS_SEXO


def _parece_edad(texto: str | None) -> bool:
    if texto is None:
        return False
    normalizado = texto.strip().upper()
    if normalizado == "RN":
        return True
    return bool(_PATRON_DIGITOS.search(normalizado))


def _parsear_edad(edad_raw: str | None) -> float | None:
    if edad_raw is None:
        return None
    normalizado = edad_raw.strip().upper()
    if normalizado == "RN":
        return 0.0
    if _PATRON_MESES.fullmatch(normalizado) or _PATRON_DIAS.fullmatch(normalizado):
        return 0.0
    if normalizado.isdigit():
        return float(normalizado)
    match = _PATRON_DIGITOS.search(normalizado)
    if match:
        return float(match.group())
    return None


def _parsear_sexo(sexo_raw: str | None) -> Sexo:
    if sexo_raw is None or not sexo_raw.strip():
        return "INDETERMINADO"
    normalizado = sexo_raw.strip().upper()
    if normalizado == "F":
        return "F"
    if normalizado == "M":
        return "M"
    return "OTRO"


def unificar_demografia(edad_raw: str | None, sexo_raw: str | None) -> tuple[float, Sexo]:
    """Consolida edad/sexo (FR-004), corrigiendo el intercambio sexo↔edad
    documentado en docs/audit_legacy.md, y aplicando los sentinels del Edge
    Case de spec.md (`-1.0`/`INDETERMINADO`) cuando ambos son nulos."""
    if _es_codigo_sexo(edad_raw) and _parece_edad(sexo_raw):
        edad_raw, sexo_raw = sexo_raw, edad_raw

    edad = _parsear_edad(edad_raw)
    edad_final = -1.0 if edad is None else edad
    sexo_final = _parsear_sexo(sexo_raw)
    return edad_final, sexo_final
