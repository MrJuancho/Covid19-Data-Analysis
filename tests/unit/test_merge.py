from datetime import datetime

from covid_analytics.cleaning.merge import cruzar_seguimiento_nominal
from covid_analytics.models import CasoUnificadoSilver

PACIENTE_ID = "a" * 64
OTRO_PACIENTE_ID = "b" * 64


def _ambulatorio(
    paciente_id: str = PACIENTE_ID,
    edad: float = 30.0,
    sexo: str = "F",
    fecha_notificacion: datetime | None = datetime(2020, 3, 18),
) -> CasoUnificadoSilver:
    return CasoUnificadoSilver(
        paciente_id=paciente_id,
        edad=edad,
        sexo=sexo,  # type: ignore[arg-type]
        municipio_residencia="OTROS",
        derechohabiencia="NINGUNO",
        fecha_notificacion=fecha_notificacion,
        resultado_prueba="POSITIVO",
        estatus_paciente="AMBULATORIO",
    )


def _hospitalizado(
    paciente_id: str = PACIENTE_ID,
    edad: float = 30.0,
    sexo: str = "F",
    fecha_ingreso_hospital: datetime | None = datetime(2020, 3, 22),
    hospital: str = "Hospital Sintetico",
) -> CasoUnificadoSilver:
    return CasoUnificadoSilver(
        paciente_id=paciente_id,
        edad=edad,
        sexo=sexo,  # type: ignore[arg-type]
        municipio_residencia="OTROS",
        derechohabiencia="NINGUNO",
        hospital=hospital,
        fecha_ingreso_hospital=fecha_ingreso_hospital,
        resultado_prueba="POSITIVO",
        estatus_paciente="NO_ESPECIFICADO",
    )


def test_cruzar_fusiona_dentro_de_ventana_de_7_dias() -> None:
    resultado = cruzar_seguimiento_nominal([_ambulatorio(), _hospitalizado()])

    assert resultado.cruces_exitosos == 1
    assert resultado.registros_huerfanos == 0
    assert len(resultado.casos) == 1
    fusionado = resultado.casos[0]
    assert fusionado.es_registro_unificado is True
    assert fusionado.estatus_paciente == "HOSPITALIZADO"
    assert fusionado.dias_entre_notificacion_e_ingreso == 4


def test_cruzar_no_fusiona_fuera_de_ventana_de_7_dias() -> None:
    hospitalizado_lejano = _hospitalizado(fecha_ingreso_hospital=datetime(2020, 4, 1))
    resultado = cruzar_seguimiento_nominal([_ambulatorio(), hospitalizado_lejano])

    assert resultado.cruces_exitosos == 0
    assert resultado.registros_huerfanos == 2
    assert len(resultado.casos) == 2
    assert all(not c.es_registro_unificado for c in resultado.casos)


def test_cruzar_resuelve_colision_por_menor_delta_t() -> None:
    ambulatorio = _ambulatorio()
    hospitalizado_cercano = _hospitalizado(fecha_ingreso_hospital=datetime(2020, 3, 20))
    hospitalizado_lejano = _hospitalizado(fecha_ingreso_hospital=datetime(2020, 3, 23))

    resultado = cruzar_seguimiento_nominal(
        [ambulatorio, hospitalizado_cercano, hospitalizado_lejano]
    )

    assert resultado.cruces_exitosos == 1
    assert resultado.colisiones_llave_sintetica == 1
    fusionado = next(c for c in resultado.casos if c.es_registro_unificado)
    assert fusionado.dias_entre_notificacion_e_ingreso == 2


def test_cruzar_pacientes_distintos_no_se_mezclan() -> None:
    resultado = cruzar_seguimiento_nominal(
        [_ambulatorio(paciente_id=PACIENTE_ID), _hospitalizado(paciente_id=OTRO_PACIENTE_ID)]
    )

    assert resultado.cruces_exitosos == 0
    assert resultado.registros_huerfanos == 2
