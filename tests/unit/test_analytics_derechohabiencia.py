from covid_analytics.analytics.derechohabiencia import (
    CATALOGO_DERECHOHABIENCIA,
    calcular_metricas_derechohabiencia,
    estandarizar_derechohabiencia,
)
from tests.fixtures.silver_sintetico import construir_silver_sintetico


def test_estandarizar_derechohabiencia_reconoce_catalogo_case_insensitive() -> None:
    assert estandarizar_derechohabiencia("imss") == "IMSS"
    assert estandarizar_derechohabiencia("Issste") == "ISSSTE"
    assert estandarizar_derechohabiencia("issemym") == "ISSEMYM"
    assert estandarizar_derechohabiencia("insabi") == "INSABI"
    assert estandarizar_derechohabiencia("privada") == "PRIVADO"


def test_estandarizar_derechohabiencia_sentinel_ninguno_mapea_a_ninguna() -> None:
    assert estandarizar_derechohabiencia("NINGUNO") == "NINGUNA"
    assert estandarizar_derechohabiencia("NINGUNA") == "NINGUNA"


def test_estandarizar_derechohabiencia_valor_no_reconocido_mapea_a_otra() -> None:
    assert estandarizar_derechohabiencia("SEDENA") == "OTRA"
    assert estandarizar_derechohabiencia("algo raro sin catalogar") == "OTRA"


def test_catalogo_derechohabiencia_contiene_las_7_categorias() -> None:
    assert set(CATALOGO_DERECHOHABIENCIA) == {
        "IMSS",
        "ISSSTE",
        "ISSEMYM",
        "INSABI",
        "PRIVADO",
        "NINGUNA",
        "OTRA",
    }


def test_calcular_metricas_derechohabiencia_consistencia_marginal() -> None:
    df = construir_silver_sintetico(
        [
            {
                "derechohabiencia": "IMSS",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "HOSPITALIZADO",
            },
            {
                "derechohabiencia": "imss",
                "resultado_prueba": "NEGATIVO",
                "estatus_paciente": "AMBULATORIO",
            },
            {
                "derechohabiencia": "SEDENA",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "DEFUNCION",
            },
            {
                "derechohabiencia": "NINGUNO",
                "resultado_prueba": "PENDIENTE",
                "estatus_paciente": "NO_ESPECIFICADO",
            },
        ]
    )
    cubo = calcular_metricas_derechohabiencia(df)
    assert cubo["total_casos"].sum() == len(df)
    assert set(cubo["derechohabiencia"]) <= set(CATALOGO_DERECHOHABIENCIA)
    assert "OTRA" in set(cubo["derechohabiencia"])  # SEDENA -> OTRA


def test_calcular_metricas_derechohabiencia_tasas_por_grupo() -> None:
    filas = (
        [
            {
                "derechohabiencia": "IMSS",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "HOSPITALIZADO",
            }
            for _ in range(2)
        ]
        + [
            {
                "derechohabiencia": "IMSS",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "AMBULATORIO",
            }
            for _ in range(1)
        ]
        + [
            {
                "derechohabiencia": "IMSS",
                "resultado_prueba": "NEGATIVO",
                "estatus_paciente": "AMBULATORIO",
            }
            for _ in range(7)
        ]
    )
    df = construir_silver_sintetico(filas)
    cubo = calcular_metricas_derechohabiencia(df)

    fila = cubo[
        (cubo["derechohabiencia"] == "IMSS")
        & (cubo["resultado_prueba"] == "POSITIVO")
        & (cubo["estatus_paciente"] == "HOSPITALIZADO")
    ].iloc[0]
    assert fila["total_casos"] == 2
    assert round(fila["tasa_positividad_grupo"], 4) == 0.3
    assert round(fila["tasa_hospitalizacion_grupo"], 4) == round(2 / 3, 4)
    assert fila["tasa_letalidad_grupo"] == 0.0


def test_calcular_metricas_derechohabiencia_division_por_cero_segura() -> None:
    df = construir_silver_sintetico(
        [
            {
                "derechohabiencia": "PRIVADO",
                "resultado_prueba": "PENDIENTE",
                "estatus_paciente": "AMBULATORIO",
            }
        ]
    )
    cubo = calcular_metricas_derechohabiencia(df)
    fila = cubo[cubo["derechohabiencia"] == "PRIVADO"].iloc[0]
    assert fila["tasa_positividad_grupo"] == 0.0
    assert fila["tasa_hospitalizacion_grupo"] == 0.0
    assert fila["tasa_letalidad_grupo"] == 0.0
