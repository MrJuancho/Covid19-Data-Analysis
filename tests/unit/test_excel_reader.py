from pathlib import Path

from covid_analytics.ingestion.excel_reader import leer_hoja_acotada
from tests.fixtures.excel_sintetico import (
    NOMINAL_FILAS_ENCABEZADO,
    SEGUIMIENTO_COLUMNS,
    construir_excel_sintetico,
)


def test_leer_hoja_acotada_encuentra_encabezado_por_texto(tmp_path: Path) -> None:
    filas = [
        {
            "NO. (consecutivo)": 1,
            "CASO (nombre,apellido paterno, apellido materno)": "Nombre Sintetico Uno",
            "SEXO (M/F)": "F",
        },
        {
            "NO. (consecutivo)": 2,
            "CASO (nombre,apellido paterno, apellido materno)": "Nombre Sintetico Dos",
            "SEXO (M/F)": "M",
        },
    ]
    destino = construir_excel_sintetico(tmp_path / "sintetico.xlsx", filas, [])

    df = leer_hoja_acotada(
        destino,
        sheet_name="SEGUIMIENTO DE CASOS COVID 19",
        columnas_clave=["NO. (consecutivo)", "CASO"],
    )

    assert list(df.columns) == SEGUIMIENTO_COLUMNS
    assert len(df) == 2
    assert df.iloc[0]["CASO (nombre,apellido paterno, apellido materno)"] == "Nombre Sintetico Uno"


def test_leer_hoja_acotada_corta_antes_del_rango_fantasma(tmp_path: Path) -> None:
    filas = [
        {
            "NO. (consecutivo)": i,
            "CASO (nombre,apellido paterno, apellido materno)": f"Sintetico {i}",
            "SEXO (M/F)": "F",
        }
        for i in range(1, 6)
    ]
    destino = construir_excel_sintetico(
        tmp_path / "sintetico.xlsx", filas, [], simular_rango_fantasma=True
    )

    df = leer_hoja_acotada(
        destino,
        sheet_name="SEGUIMIENTO DE CASOS COVID 19",
        columnas_clave=["NO. (consecutivo)", "CASO"],
    )

    # Debe detenerse en la fila real de datos (5), no arrastrar el rango
    # fantasma de ~100,000 filas simulado por construir_excel_sintetico.
    assert len(df) == 5


def test_leer_hoja_acotada_hoja_nominal_encabezado_combinado(tmp_path: Path) -> None:
    filas_nominal = [
        {
            "HOSPITAL": "Hospital Sintetico",
            "NO.": 1,
            "NOMBRE DEL PACIENTE": "Paciente Uno",
            "F": "30",
        },
    ]
    destino = construir_excel_sintetico(tmp_path / "sintetico.xlsx", [], filas_nominal)

    df = leer_hoja_acotada(
        destino,
        sheet_name=" NOMINAL DE HOSPITALIZADOS",
        columnas_clave=["HOSPITAL", "NOMBRE DEL PACIENTE"],
        filas_encabezado=NOMINAL_FILAS_ENCABEZADO,
    )

    assert len(df) == 1
    assert list(df.columns).count("HOSPITAL") == 1
    # El encabezado de 2 niveles (EDAD/F, EDAD/M) se combina con " | ",
    # propagando la etiqueta de grupo por las celdas combinadas de Excel.
    assert "EDAD | F" in df.columns
    assert str(df.iloc[0]["EDAD | F"]) == "30"
