"""Orquestación de la capa Silver: normalización + (más adelante) cruce heurístico."""

from __future__ import annotations

from dataclasses import dataclass

from covid_analytics.cleaning.catalogos import (
    estandarizar_estatus_paciente,
    estandarizar_municipio,
    estandarizar_resultado_prueba,
)
from covid_analytics.cleaning.demografia import unificar_demografia
from covid_analytics.cleaning.fechas import (
    corregir_resultado_fecha_intercambiados,
    parse_fecha_con_telemetria,
)
from covid_analytics.cleaning.merge import cruzar_seguimiento_nominal
from covid_analytics.models import CasoBronze, CasoUnificadoSilver


@dataclass(frozen=True)
class ResultadoLimpieza:
    casos: list[CasoUnificadoSilver]
    correcciones_columnas_intercambiadas: int
    cruces_exitosos: int
    registros_huerfanos: int
    colisiones_llave_sintetica: int
    fechas_anomalas_fuera_ventana: int


def _caso_bronze_a_silver(caso: CasoBronze) -> tuple[CasoUnificadoSilver, bool, int]:
    resultado_raw, fecha_resultado_raw = corregir_resultado_fecha_intercambiados(
        caso.resultado_raw, caso.fecha_resultado_raw
    )
    hubo_correccion = resultado_raw != caso.resultado_raw

    edad, sexo = unificar_demografia(caso.edad_raw, caso.sexo_raw)

    fecha_notificacion, anomalia_notificacion = parse_fecha_con_telemetria(
        caso.fecha_notificacion_raw
    )
    fecha_toma_muestra, anomalia_toma_muestra = parse_fecha_con_telemetria(
        caso.fecha_toma_muestra_raw
    )
    fecha_resultado, anomalia_resultado = parse_fecha_con_telemetria(fecha_resultado_raw)
    fecha_ingreso_hospital, anomalia_ingreso = parse_fecha_con_telemetria(caso.fecha_ingreso_raw)
    fechas_anomalas = sum(
        (anomalia_notificacion, anomalia_toma_muestra, anomalia_resultado, anomalia_ingreso)
    )

    silver = CasoUnificadoSilver(
        paciente_id=caso.paciente_id,
        edad=edad,
        sexo=sexo,
        municipio_residencia=estandarizar_municipio(caso.municipio_raw),
        derechohabiencia=caso.derechohabiencia_raw or "NINGUNO",
        fecha_notificacion=fecha_notificacion,
        fecha_toma_muestra=fecha_toma_muestra,
        fecha_resultado=fecha_resultado,
        resultado_prueba=estandarizar_resultado_prueba(resultado_raw),
        estatus_paciente=estandarizar_estatus_paciente(caso.estatus_raw),
        hospital=caso.hospital_raw,
        fecha_ingreso_hospital=fecha_ingreso_hospital,
        es_registro_unificado=False,
        dias_entre_notificacion_e_ingreso=None,
    )
    return silver, hubo_correccion, fechas_anomalas


def limpiar_silver(casos_bronze: list[CasoBronze]) -> ResultadoLimpieza:
    """Normaliza cada `CasoBronze` a `CasoUnificadoSilver` (FR-004..FR-006, FR-009)
    y aplica el cruce heurístico Seguimiento↔Nominal (FR-007, `cleaning/merge.py`)."""
    casos_sin_cruzar: list[CasoUnificadoSilver] = []
    correcciones = 0
    fechas_anomalas_fuera_ventana = 0
    for caso in casos_bronze:
        silver, hubo_correccion, fechas_anomalas = _caso_bronze_a_silver(caso)
        casos_sin_cruzar.append(silver)
        if hubo_correccion:
            correcciones += 1
        fechas_anomalas_fuera_ventana += fechas_anomalas

    resultado_merge = cruzar_seguimiento_nominal(casos_sin_cruzar)

    return ResultadoLimpieza(
        casos=resultado_merge.casos,
        correcciones_columnas_intercambiadas=correcciones,
        cruces_exitosos=resultado_merge.cruces_exitosos,
        registros_huerfanos=resultado_merge.registros_huerfanos,
        colisiones_llave_sintetica=resultado_merge.colisiones_llave_sintetica,
        fechas_anomalas_fuera_ventana=fechas_anomalas_fuera_ventana,
    )
