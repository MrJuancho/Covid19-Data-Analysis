"""Normalización de nombre y hash de seudonimización de PII (FR-002, research.md #6)."""

from __future__ import annotations

import hashlib
import logging
import os
import unicodedata

logger = logging.getLogger(__name__)

_SALT_ENV_VAR = "COVID_PII_SALT"
_SALT_FALLBACK = "covid-analytics-fallback-salt-no-usar-en-produccion"


def normalizar_nombre(texto: str) -> str:
    """Mayúsculas, sin acentos/diéresis (conserva Ñ), espacios colapsados y recortados."""
    mayusculas = texto.upper()
    descompuesto = unicodedata.normalize("NFD", mayusculas)
    sin_acentos = "".join(
        char for char in descompuesto if not (unicodedata.combining(char) and char != "̃")
    )
    recompuesto = unicodedata.normalize("NFC", sin_acentos)
    return " ".join(recompuesto.split())


def generar_hash_pii(nombre: str, folio: str | int | None, salt: str) -> str:
    """SHA256(Normalizar(Nombre) + str(Folio) + Sal) — FR-002.

    Edge Case (spec.md): si `folio` es nulo/inválido, se usa una máscara
    determinista (cadena vacía) para no bloquear la ingesta.
    """
    folio_str = "" if folio is None else str(folio)
    contenido = normalizar_nombre(nombre) + folio_str + salt
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()


def obtener_salt() -> str:
    """Lee COVID_PII_SALT del entorno; si está ausente, usa un fallback
    documentado y emite un warning (research.md #6)."""
    salt = os.environ.get(_SALT_ENV_VAR)
    if not salt:
        logger.warning(
            "%s no está configurada; usando fallback determinista no apto para "
            "producción. Configure la variable de entorno para corridas reales.",
            _SALT_ENV_VAR,
        )
        return _SALT_FALLBACK
    return salt
