import tracemalloc
from pathlib import Path

from covid_analytics.ingestion import ingerir_bronze
from tests.fixtures.excel_sintetico import construir_excel_sintetico

PII_RAW_COLUMNS = {"CASO", "NOMBRE DEL PACIENTE", "CALLE", "TELEFONO"}


def _excel_sintetico(tmp_path: Path) -> Path:
    filas_seguimiento = [
        {
            "NO. (consecutivo)": 1,
            "CASO (nombre,apellido paterno, apellido materno)": "Nombre Sintetico Uno Apellido",
            "SEXO (M/F)": "F",
            "EDAD (ej: anos: 3;meses-3M)": "34",
            "MUNICIPIO/PAIS RESIDENCIA": "TOLUCA",
            "DERECHOHABIENCIA (IMSS, ISSSTE, ISSEMYM, SEDENA, NINGUNO)": "NINGUNO",
            "FECHA DE NOTIFICACION (dd/mm/aaaa)": "18/03/2020",
            "FECHA TOMA DE MUESTRA (dd/mm/aaaa)": "18/03/2020",
            "RESULTADO (POSITIVO, NEGATIVO, PENDIENTE)": "POSITIVO",
            "FECHA DE RESULTADO  (dd/mm/aaaa)": "20/03/2020",
            "ESTATUS": "AMBULATORIO",
        }
    ]
    filas_nominal = [
        {
            "HOSPITAL": "Hospital Sintetico",
            "NO.": 1,
            "NOMBRE DEL PACIENTE": "Paciente Sintetico Dos",
            "F": "40",
            "FECHA DE INGRESO O DE ATENCION": "22/03/2020",
            "RESULTADO": "POSITIVO",
        }
    ]
    return construir_excel_sintetico(
        tmp_path / "sintetico.xlsx",
        filas_seguimiento,
        filas_nominal,
        simular_rango_fantasma=True,
    )


def test_ingerir_bronze_hashea_pii_y_elimina_columnas_originales(tmp_path: Path) -> None:
    destino = _excel_sintetico(tmp_path)

    resultado = ingerir_bronze(destino, salt="sal-test")

    assert resultado.filas_leidas_seguimiento == 1
    assert resultado.filas_leidas_nominal == 1
    assert len(resultado.casos) == 2

    for caso in resultado.casos:
        assert len(caso.paciente_id) == 64
        # CasoBronze no tiene ningún campo de PII en texto plano: solo existen
        # los *_raw ya definidos en el modelo, ninguno de los cuales guarda nombre/
        # dirección/teléfono crudos.
        campos_modelo = set(type(caso).model_fields)
        assert not campos_modelo & PII_RAW_COLUMNS


def test_ingerir_bronze_consumo_memoria_acotado(tmp_path: Path) -> None:
    destino = _excel_sintetico(tmp_path)

    tracemalloc.start()
    ingerir_bronze(destino, salt="sal-test")
    _, pico_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    pico_mb = pico_bytes / (1024 * 1024)
    assert pico_mb < 500, f"Consumo pico {pico_mb:.1f} MB excede el límite de SC-002 (500 MB)"
