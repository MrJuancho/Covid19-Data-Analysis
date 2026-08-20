import pandas as pd

from covid_analytics.analytics.demografia import (
    GRUPOS_EDAD_CANONICOS,
    asignar_grupo_edad,
    asignar_grupo_edad_ui,
    calcular_metricas_demografia,
)
from tests.fixtures.silver_sintetico import construir_silver_sintetico


def test_asignar_grupo_edad_clasifica_los_14_rangos_canonicos() -> None:
    edades = pd.Series([0.0, 1.0, 2.0, 11.0, 12.0, 17.0, 18.0, 24.0, 66.0, 90.0, -1.0])
    grupos = asignar_grupo_edad(edades)

    assert list(grupos) == [
        "0-1",
        "0-1",
        "2-11",
        "2-11",
        "12-17",
        "12-17",
        "18-24",
        "18-24",
        "66+",
        "66+",
        "SIN_DATO",
    ]


def test_asignar_grupo_edad_usa_sin_dato_para_sentinel_y_nulos() -> None:
    edades = pd.Series([-1.0, None])
    grupos = asignar_grupo_edad(edades)
    assert list(grupos) == ["SIN_DATO", "SIN_DATO"]


def test_calcular_metricas_demografia_preserva_grupos_etarios_vacios() -> None:
    df = construir_silver_sintetico(
        [
            {
                "edad": 30.0,
                "sexo": "F",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "AMBULATORIO",
            }
        ]
    )
    cubo = calcular_metricas_demografia(df)

    assert set(GRUPOS_EDAD_CANONICOS) <= set(cubo["grupo_edad"])
    fila_vacia = cubo[(cubo["grupo_edad"] == "0-1") & (cubo["sexo"] == "F")]
    assert (fila_vacia["total_casos"] == 0).all()
    assert (fila_vacia["porcentaje_del_total"] == 0.0).all()


def test_calcular_metricas_demografia_tasa_positividad_excluye_pendientes() -> None:
    filas = (
        [
            {
                "edad": 31.0,
                "sexo": "F",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "AMBULATORIO",
            }
            for _ in range(30)
        ]
        + [
            {
                "edad": 31.0,
                "sexo": "F",
                "resultado_prueba": "NEGATIVO",
                "estatus_paciente": "AMBULATORIO",
            }
            for _ in range(70)
        ]
        + [
            {
                "edad": 31.0,
                "sexo": "F",
                "resultado_prueba": "PENDIENTE",
                "estatus_paciente": "AMBULATORIO",
            }
            for _ in range(10)
        ]
    )
    df = construir_silver_sintetico(filas)
    cubo = calcular_metricas_demografia(df)

    fila_positivos = cubo[
        (cubo["grupo_edad"] == "31-35")
        & (cubo["sexo"] == "F")
        & (cubo["resultado_prueba"] == "POSITIVO")
    ]
    assert fila_positivos["tasa_positividad_grupo"].iloc[0] == 0.30
    assert fila_positivos["total_casos"].iloc[0] == 30


def test_calcular_metricas_demografia_consistencia_marginal() -> None:
    df = construir_silver_sintetico(
        [
            {
                "edad": 10.0,
                "sexo": "M",
                "resultado_prueba": "NEGATIVO",
                "estatus_paciente": "AMBULATORIO",
            },
            {
                "edad": 45.0,
                "sexo": "OTRO",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "DEFUNCION",
            },
            {
                "edad": -1.0,
                "sexo": "INDETERMINADO",
                "resultado_prueba": "NO_CONCLUYENTE",
                "estatus_paciente": "NO_ESPECIFICADO",
            },
        ]
    )
    cubo = calcular_metricas_demografia(df)
    assert cubo["total_casos"].sum() == len(df)


def test_asignar_grupo_edad_ui_clasifica_con_cortes_exactos() -> None:
    edades = pd.Series([0.0, 17.0, 18.0, 39.0, 40.0, 59.0, 60.0, 90.0, -1.0])
    grupos = asignar_grupo_edad_ui(edades)
    assert list(grupos) == [
        "<18",
        "<18",
        "18-39",
        "18-39",
        "40-59",
        "40-59",
        "60+",
        "60+",
        "SIN_DATO",
    ]


def test_asignar_grupo_edad_ui_resuelve_desalineacion_de_bins_36_40_y_56_60() -> None:
    # /speckit-clarify (spec.md): los bins canónicos "36-40" y "56-60" cruzan los
    # cortes de 40 y 60 años; grupo_edad_ui NO debe heredar ese error de redondeo.
    edades = pd.Series([36.0, 39.0, 40.0, 56.0, 59.0, 60.0])
    grupos_canonicos = asignar_grupo_edad(edades)
    grupos_ui = asignar_grupo_edad_ui(edades)

    assert list(grupos_canonicos) == ["36-40", "36-40", "36-40", "56-60", "56-60", "56-60"]
    assert list(grupos_ui) == ["18-39", "18-39", "40-59", "40-59", "40-59", "60+"]


def test_calcular_metricas_demografia_incluye_grupo_edad_ui_consistente() -> None:
    df = construir_silver_sintetico(
        [
            {
                "edad": 36.0,
                "sexo": "F",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "AMBULATORIO",
            },
            {
                "edad": 40.0,
                "sexo": "F",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "AMBULATORIO",
            },
            {
                "edad": 56.0,
                "sexo": "M",
                "resultado_prueba": "NEGATIVO",
                "estatus_paciente": "AMBULATORIO",
            },
            {
                "edad": 60.0,
                "sexo": "M",
                "resultado_prueba": "NEGATIVO",
                "estatus_paciente": "AMBULATORIO",
            },
            {
                "edad": -1.0,
                "sexo": "OTRO",
                "resultado_prueba": "PENDIENTE",
                "estatus_paciente": "NO_ESPECIFICADO",
            },
        ]
    )
    cubo = calcular_metricas_demografia(df)

    assert "grupo_edad_ui" in cubo.columns
    assert cubo["total_casos"].sum() == len(df)

    fila_36 = cubo[
        (cubo["grupo_edad"] == "36-40") & (cubo["sexo"] == "F") & (cubo["total_casos"] > 0)
    ]
    assert set(fila_36["grupo_edad_ui"]) == {"18-39", "40-59"}

    # grupo_edad = SIN_DATO <=> grupo_edad_ui = SIN_DATO (misma sentinel de origen).
    filas_sin_dato = cubo[cubo["total_casos"] > 0]
    for _, fila in filas_sin_dato.iterrows():
        assert (fila["grupo_edad"] == "SIN_DATO") == (fila["grupo_edad_ui"] == "SIN_DATO")
