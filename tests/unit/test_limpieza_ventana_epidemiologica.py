from covid_analytics.cleaning import limpiar_silver
from covid_analytics.models import CasoBronze

PACIENTE_ID = "a" * 64


def _caso_bronze(**overrides: object) -> CasoBronze:
    base: dict[str, object] = {
        "paciente_id": PACIENTE_ID,
        "fuente": "seguimiento",
        "sexo_raw": "F",
        "edad_raw": "30",
        "resultado_raw": "POSITIVO",
        "fecha_notificacion_raw": "18/03/2020",
    }
    base.update(overrides)
    return CasoBronze(**base)  # type: ignore[arg-type]


def test_limpiar_silver_cuenta_fechas_anomalas_fuera_de_ventana() -> None:
    # "0208" no es un typo conocido, pero igual queda fuera de la ventana
    # epidemiológica tras el parseo -> se telemetra como anomalía.
    resultado = limpiar_silver([_caso_bronze(fecha_notificacion_raw="0208-05-15")])

    assert resultado.fechas_anomalas_fuera_ventana == 1
    assert resultado.casos[0].fecha_notificacion is None


def test_limpiar_silver_corrige_typo_de_anio_sin_contarlo_como_anomalia() -> None:
    resultado = limpiar_silver([_caso_bronze(fecha_notificacion_raw="0202-05-15")])

    assert resultado.fechas_anomalas_fuera_ventana == 0
    assert resultado.casos[0].fecha_notificacion is not None
    assert resultado.casos[0].fecha_notificacion.year == 2020


def test_limpiar_silver_sin_fechas_anomalas_reporta_cero() -> None:
    resultado = limpiar_silver([_caso_bronze()])
    assert resultado.fechas_anomalas_fuera_ventana == 0


def test_limpiar_silver_acumula_anomalias_en_multiples_columnas_y_casos() -> None:
    casos = [
        _caso_bronze(
            fecha_notificacion_raw="0208-05-15",
            fecha_toma_muestra_raw="0208-05-16",
        ),
        _caso_bronze(fecha_resultado_raw="0208-05-20"),
    ]
    resultado = limpiar_silver(casos)
    assert resultado.fechas_anomalas_fuera_ventana == 3
