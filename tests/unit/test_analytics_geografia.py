from covid_analytics.analytics.geografia import calcular_distribucion_geografica
from tests.fixtures.silver_sintetico import construir_silver_sintetico


def test_calcular_distribucion_geografica_agrega_por_municipio() -> None:
    filas = (
        [
            {
                "municipio_residencia": "ECATEPEC",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "DEFUNCION",
            }
        ]
        * 2
        + [
            {
                "municipio_residencia": "ECATEPEC",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "HOSPITALIZADO",
            }
        ]
        * 1
        + [
            {
                "municipio_residencia": "ECATEPEC",
                "resultado_prueba": "NEGATIVO",
                "estatus_paciente": "AMBULATORIO",
            }
        ]
        * 7
    )
    df = construir_silver_sintetico(filas)
    geo = calcular_distribucion_geografica(df)

    fila = geo[geo["municipio_residencia"] == "ECATEPEC"].iloc[0]
    assert fila["total_casos"] == 10
    assert fila["total_positivos"] == 3
    assert fila["total_negativos"] == 7
    assert fila["total_defunciones"] == 2
    assert fila["total_hospitalizados"] == 1
    assert fila["tasa_positividad"] == 0.3
    assert round(fila["tasa_letalidad"], 4) == round(2 / 3, 4)
    assert round(fila["tasa_hospitalizacion"], 4) == round(1 / 3, 4)


def test_calcular_distribucion_geografica_division_por_cero_segura() -> None:
    filas = [
        {
            "municipio_residencia": "LA PAZ",
            "resultado_prueba": "PENDIENTE",
            "estatus_paciente": "AMBULATORIO",
        }
    ]
    df = construir_silver_sintetico(filas)
    geo = calcular_distribucion_geografica(df)

    fila = geo[geo["municipio_residencia"] == "LA PAZ"].iloc[0]
    assert fila["total_positivos"] == 0
    assert fila["tasa_positividad"] == 0.0
    assert fila["tasa_letalidad"] == 0.0
    assert fila["tasa_hospitalizacion"] == 0.0


def test_calcular_distribucion_geografica_consistencia_marginal() -> None:
    filas = [
        {"municipio_residencia": "NEZAHUALCOYOTL"},
        {"municipio_residencia": "CHIMALHUACAN"},
        {"municipio_residencia": "OTROS"},
    ]
    df = construir_silver_sintetico(filas)
    geo = calcular_distribucion_geografica(df)
    assert geo["total_casos"].sum() == len(df)
