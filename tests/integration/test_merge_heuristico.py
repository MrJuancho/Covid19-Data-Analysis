from pathlib import Path

from covid_analytics.cleaning import limpiar_silver
from covid_analytics.ingestion import ingerir_bronze
from tests.fixtures.excel_sintetico import construir_excel_sintetico


def test_pipeline_completo_fusiona_seguimiento_y_nominal(tmp_path: Path) -> None:
    # spec.md User Story 3, Independent Test: mismo paciente_id (mismo folio +
    # nombre normalizado), notificado 2020-03-18, ingresado 2020-03-22 -> se
    # unifica en un único registro con estatus final HOSPITALIZADO.
    filas_seguimiento = [
        {
            "NO. (consecutivo)": 1,
            "CASO (nombre,apellido paterno, apellido materno)": "Paciente Sintetico Compartido",
            "SEXO (M/F)": "F",
            "EDAD (ej: anos: 3;meses-3M)": "30",
            "FECHA DE NOTIFICACION (dd/mm/aaaa)": "18/03/2020",
            "RESULTADO (POSITIVO, NEGATIVO, PENDIENTE)": "POSITIVO",
        }
    ]
    filas_nominal = [
        {
            "HOSPITAL": "Hospital Sintetico",
            "NO.": 1,
            "NOMBRE DEL PACIENTE": "Paciente Sintetico Compartido",
            "F": "30",
            "FECHA DE INGRESO O DE ATENCION": "22/03/2020",
        }
    ]
    destino = construir_excel_sintetico(
        tmp_path / "sintetico.xlsx", filas_seguimiento, filas_nominal
    )

    resultado_ingesta = ingerir_bronze(destino, salt="sal-test")
    resultado_limpieza = limpiar_silver(resultado_ingesta.casos)

    assert resultado_limpieza.cruces_exitosos == 1
    assert resultado_limpieza.registros_huerfanos == 0
    assert len(resultado_limpieza.casos) == 1

    fusionado = resultado_limpieza.casos[0]
    assert fusionado.es_registro_unificado is True
    assert fusionado.estatus_paciente == "HOSPITALIZADO"
    assert fusionado.dias_entre_notificacion_e_ingreso == 4
    assert fusionado.hospital == "Hospital Sintetico"
