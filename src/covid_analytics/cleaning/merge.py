"""Cruce heurístico Seguimiento↔Nominal por llave sintética (FR-007)."""

from __future__ import annotations

from dataclasses import dataclass

from covid_analytics.models import CasoUnificadoSilver

_VENTANA_MAXIMA_DIAS = 7


@dataclass(frozen=True)
class ResultadoMerge:
    casos: list[CasoUnificadoSilver]
    cruces_exitosos: int
    registros_huerfanos: int
    colisiones_llave_sintetica: int


def _es_ambulatorio(caso: CasoUnificadoSilver) -> bool:
    return caso.fecha_notificacion is not None


def _es_hospitalizado(caso: CasoUnificadoSilver) -> bool:
    return caso.fecha_ingreso_hospital is not None


def _llave(caso: CasoUnificadoSilver) -> tuple[str, float, str]:
    return caso.paciente_id, caso.edad, caso.sexo


def _fusionar(
    ambulatorio: CasoUnificadoSilver, hospitalizado: CasoUnificadoSilver, dias: int
) -> CasoUnificadoSilver:
    return ambulatorio.model_copy(
        update={
            "hospital": hospitalizado.hospital,
            "fecha_ingreso_hospital": hospitalizado.fecha_ingreso_hospital,
            "estatus_paciente": "HOSPITALIZADO",
            "es_registro_unificado": True,
            "dias_entre_notificacion_e_ingreso": dias,
        }
    )


def cruzar_seguimiento_nominal(casos: list[CasoUnificadoSilver]) -> ResultadoMerge:
    """Vincula registros ambulatorios (Seguimiento) con admisiones hospitalarias
    (Nominal) mediante la llave sintética `paciente_id + edad + sexo` y una
    ventana temporal máxima de 7 días (FR-007). Resuelve colisiones de
    homónimos por menor diferencia absoluta de días (Edge Case, spec.md)."""
    ambulatorios = [c for c in casos if _es_ambulatorio(c)]
    hospitalizados = [c for c in casos if _es_hospitalizado(c)]
    otros = [c for c in casos if not _es_ambulatorio(c) and not _es_hospitalizado(c)]

    hospitalizados_por_llave: dict[tuple[str, float, str], list[CasoUnificadoSilver]] = {}
    for h in hospitalizados:
        hospitalizados_por_llave.setdefault(_llave(h), []).append(h)

    fusionados: list[CasoUnificadoSilver] = []
    hospitalizados_usados: set[int] = set()
    colisiones = 0

    for ambulatorio in ambulatorios:
        candidatos = hospitalizados_por_llave.get(_llave(ambulatorio), [])
        assert ambulatorio.fecha_notificacion is not None
        emparejados: list[tuple[int, CasoUnificadoSilver]] = []
        for h in candidatos:
            if id(h) in hospitalizados_usados:
                continue
            assert h.fecha_ingreso_hospital is not None
            dias = abs((h.fecha_ingreso_hospital - ambulatorio.fecha_notificacion).days)
            if dias <= _VENTANA_MAXIMA_DIAS:
                emparejados.append((dias, h))

        if not emparejados:
            fusionados.append(ambulatorio)
            continue

        if len(emparejados) > 1:
            colisiones += 1
        dias_minimos, mejor_candidato = min(emparejados, key=lambda par: par[0])
        hospitalizados_usados.add(id(mejor_candidato))
        fusionados.append(_fusionar(ambulatorio, mejor_candidato, dias_minimos))

    huerfanos_hospitalizados = [h for h in hospitalizados if id(h) not in hospitalizados_usados]

    casos_finales = fusionados + huerfanos_hospitalizados + otros
    cruces_exitosos = sum(1 for c in casos_finales if c.es_registro_unificado)
    registros_huerfanos = len(casos_finales) - cruces_exitosos

    return ResultadoMerge(
        casos=casos_finales,
        cruces_exitosos=cruces_exitosos,
        registros_huerfanos=registros_huerfanos,
        colisiones_llave_sintetica=colisiones,
    )
