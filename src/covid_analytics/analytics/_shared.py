"""Utilidades compartidas de la capa Gold (Principio II)."""

from __future__ import annotations


class GoldIntegrityError(Exception):
    """Se lanza cuando una tabla Gold viola la consistencia marginal con Silver (FR-007)."""


def tasa_segura(numerador: float, denominador: float) -> float:
    """Calcula `numerador / denominador`, retornando `0.0` si el denominador es 0."""
    if denominador == 0:
        return 0.0
    return numerador / denominador
