"""Contratos Pydantic de datos (data-model.md)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Literal

from pydantic import BaseModel, Field

Sexo = Literal["F", "M", "OTRO", "INDETERMINADO"]
ResultadoPrueba = Literal["POSITIVO", "NEGATIVO", "PENDIENTE", "NO_CONCLUYENTE", "NO_ESPECIFICADO"]
EstatusPaciente = Literal["AMBULATORIO", "HOSPITALIZADO", "DEFUNCION", "NO_ESPECIFICADO"]
FuenteBronze = Literal["seguimiento", "nominal"]
GrupoEdad = Literal[
    "0-1",
    "2-11",
    "12-17",
    "18-24",
    "25-30",
    "31-35",
    "36-40",
    "41-45",
    "46-50",
    "51-55",
    "56-60",
    "61-65",
    "66+",
    "SIN_DATO",
]
GrupoEdadUi = Literal["<18", "18-39", "40-59", "60+", "SIN_DATO"]
DerechohabienciaGold = Literal["IMSS", "ISSSTE", "ISSEMYM", "INSABI", "PRIVADO", "NINGUNA", "OTRA"]


class CasoBronze(BaseModel):
    """Estructura intermedia en memoria, posterior a la ingesta cruda + hash de PII.

    Nunca se persiste a disco (Principio I de la Constitución).
    """

    paciente_id: str = Field(min_length=64, max_length=64)
    fuente: FuenteBronze
    folio_origen: str | None = None
    sexo_raw: str | None = None
    edad_raw: str | None = None
    municipio_raw: str | None = None
    derechohabiencia_raw: str | None = None
    fecha_notificacion_raw: datetime | int | str | None = None
    fecha_toma_muestra_raw: datetime | int | str | None = None
    resultado_raw: str | None = None
    fecha_resultado_raw: datetime | int | str | None = None
    estatus_raw: str | None = None
    fecha_ingreso_raw: datetime | int | str | None = None
    hospital_raw: str | None = None


class CasoUnificadoSilver(BaseModel):
    """Entidad limpia y tipada, contrato persistido en casos_unificados.parquet."""

    paciente_id: str = Field(min_length=64, max_length=64)
    edad: float = Field(ge=-1.0)
    sexo: Sexo
    municipio_residencia: str
    derechohabiencia: str
    fecha_notificacion: datetime | None = None
    fecha_toma_muestra: datetime | None = None
    fecha_resultado: datetime | None = None
    resultado_prueba: ResultadoPrueba
    estatus_paciente: EstatusPaciente
    hospital: str | None = None
    fecha_ingreso_hospital: datetime | None = None
    es_registro_unificado: bool = False
    dias_entre_notificacion_e_ingreso: int | None = None


class ResumenCalidad(BaseModel):
    """Registro de telemetría persistido en data_quality_summary.json."""

    filas_leidas_bronze_seguimiento: int = Field(ge=0)
    filas_leidas_bronze_nominal: int = Field(ge=0)
    registros_hasheados: int = Field(ge=0)
    cruces_exitosos: int = Field(ge=0)
    registros_huerfanos: int = Field(ge=0)
    porcentaje_huerfanos: float = Field(ge=0.0)
    correcciones_columnas_intercambiadas: int = Field(ge=0)
    colisiones_llave_sintetica: int = Field(ge=0)
    fechas_anomalas_fuera_ventana: int = Field(ge=0)
    timestamp_ejecucion: datetime


def construir_resumen_calidad(
    *,
    filas_leidas_bronze_seguimiento: int,
    filas_leidas_bronze_nominal: int,
    registros_hasheados: int,
    cruces_exitosos: int,
    registros_huerfanos: int,
    correcciones_columnas_intercambiadas: int,
    colisiones_llave_sintetica: int,
    fechas_anomalas_fuera_ventana: int = 0,
) -> ResumenCalidad:
    """Construye `ResumenCalidad`, calculando `porcentaje_huerfanos` sin
    dividir entre cero (SC-003: ninguna métrica en nulo)."""
    total = cruces_exitosos + registros_huerfanos
    porcentaje_huerfanos = registros_huerfanos / total if total > 0 else 0.0
    return ResumenCalidad(
        filas_leidas_bronze_seguimiento=filas_leidas_bronze_seguimiento,
        filas_leidas_bronze_nominal=filas_leidas_bronze_nominal,
        registros_hasheados=registros_hasheados,
        cruces_exitosos=cruces_exitosos,
        registros_huerfanos=registros_huerfanos,
        porcentaje_huerfanos=porcentaje_huerfanos,
        correcciones_columnas_intercambiadas=correcciones_columnas_intercambiadas,
        colisiones_llave_sintetica=colisiones_llave_sintetica,
        fechas_anomalas_fuera_ventana=fechas_anomalas_fuera_ventana,
        timestamp_ejecucion=datetime.now(UTC),
    )


class MetricasDemografiaGold(BaseModel):
    """Fila del cubo (grupo_edad x grupo_edad_ui x sexo x resultado_prueba x estatus_paciente)."""

    grupo_edad: GrupoEdad
    grupo_edad_ui: GrupoEdadUi
    sexo: Sexo
    resultado_prueba: ResultadoPrueba
    estatus_paciente: EstatusPaciente
    total_casos: int = Field(ge=0)
    porcentaje_del_total: float = Field(ge=0.0, le=1.0)
    tasa_positividad_grupo: float = Field(ge=0.0, le=1.0)


class SeriesTemporalesGold(BaseModel):
    """Fila diaria de la serie temporal continua de la capa Gold."""

    fecha: date
    casos_notificados: int = Field(ge=0)
    pruebas_tomadas: int = Field(ge=0)
    resultados_positivos: int = Field(ge=0)
    resultados_negativos: int = Field(ge=0)
    ingresos_hospitalarios: int = Field(ge=0)
    defunciones: int = Field(ge=0)
    media_movil_7d_positivos: float = Field(ge=0.0)
    casos_positivos_acumulados: int = Field(ge=0)


class DistribucionGeograficaGold(BaseModel):
    """Fila agregada por `municipio_residencia`."""

    municipio_residencia: str
    total_casos: int = Field(ge=0)
    total_positivos: int = Field(ge=0)
    total_negativos: int = Field(ge=0)
    total_hospitalizados: int = Field(ge=0)
    total_defunciones: int = Field(ge=0)
    tasa_positividad: float = Field(ge=0.0, le=1.0)
    tasa_letalidad: float = Field(ge=0.0, le=1.0)
    tasa_hospitalizacion: float = Field(ge=0.0, le=1.0)


class MetricasDerechohabienciaGold(BaseModel):
    """Fila del cubo (derechohabiencia x resultado_prueba x estatus_paciente)."""

    derechohabiencia: DerechohabienciaGold
    resultado_prueba: ResultadoPrueba
    estatus_paciente: EstatusPaciente
    total_casos: int = Field(ge=0)
    porcentaje_del_total: float = Field(ge=0.0, le=1.0)
    tasa_positividad_grupo: float = Field(ge=0.0, le=1.0)
    tasa_hospitalizacion_grupo: float = Field(ge=0.0, le=1.0)
    tasa_letalidad_grupo: float = Field(ge=0.0, le=1.0)


class KpisGeneralesGold(BaseModel):
    """Fila única de KPIs macro/globales (`kpis_generales.parquet` y `resumen_ejecutivo.json`)."""

    total_pacientes_atendidos: int = Field(ge=0)
    total_positivos: int = Field(ge=0)
    total_negativos: int = Field(ge=0)
    total_pendientes: int = Field(ge=0)
    total_no_concluyentes: int = Field(ge=0)
    total_hospitalizados: int = Field(ge=0)
    total_defunciones: int = Field(ge=0)
    tasa_global_positividad: float = Field(ge=0.0, le=1.0)
    tasa_global_letalidad: float = Field(ge=0.0, le=1.0)
    tasa_global_hospitalizacion: float = Field(ge=0.0, le=1.0)
    registros_unificados_cruce: int = Field(ge=0)
    mediana_dias_notificacion_ingreso: float | None = None
    casos_fechas_invertidas: int = Field(ge=0)
    timestamp_generacion: str
