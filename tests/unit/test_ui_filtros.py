from datetime import date

from covid_analytics.ui.filtros import (
    FiltroTablero,
    aplicar_filtro_demografia,
    aplicar_filtro_derechohabiencia,
    aplicar_filtro_series,
    calcular_vista_kpi,
)
from tests.fixtures.gold_sintetico import (
    construir_kpis_generales_gold,
    construir_metricas_demografia_gold,
    construir_metricas_derechohabiencia_gold,
    construir_series_temporales_gold,
)


def _filtro(
    fecha_inicio: date = date(2021, 1, 1),
    fecha_fin: date = date(2021, 1, 1),
    sexos: tuple[str, ...] = (),
    grupos_edad_ui: tuple[str, ...] = (),
    derechohabiencias: tuple[str, ...] = (),
) -> FiltroTablero:
    return FiltroTablero(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        sexos=sexos,  # type: ignore[arg-type]
        grupos_edad_ui=grupos_edad_ui,  # type: ignore[arg-type]
        derechohabiencias=derechohabiencias,  # type: ignore[arg-type]
    )


def test_aplicar_filtro_series_recorta_al_rango_inclusive() -> None:
    df = construir_series_temporales_gold(
        [
            {"fecha": "2021-01-01"},
            {"fecha": "2021-01-02"},
            {"fecha": "2021-01-03"},
            {"fecha": "2021-01-04"},
        ]
    )
    filtro = _filtro(date(2021, 1, 2), date(2021, 1, 3))
    recortado = aplicar_filtro_series(df, filtro)
    assert list(recortado["fecha"].dt.date) == [date(2021, 1, 2), date(2021, 1, 3)]


def test_aplicar_filtro_series_fuera_de_rango_produce_vacio() -> None:
    df = construir_series_temporales_gold([{"fecha": "2021-01-01"}])
    filtro = _filtro(date(2022, 1, 1), date(2022, 1, 31))
    recortado = aplicar_filtro_series(df, filtro)
    assert recortado.empty


def test_calcular_vista_kpi_sin_filtrar_usa_kpis_generales_directamente() -> None:
    kpis_df = construir_kpis_generales_gold(
        total_pacientes_atendidos=100,
        total_positivos=30,
        tasa_global_positividad=0.3,
        tasa_global_hospitalizacion=0.1,
    )
    series = construir_series_temporales_gold([{"fecha": "2021-01-01"}])
    vista = calcular_vista_kpi(kpis_df, series, sin_filtrar=True)
    assert vista.total_pruebas == 100
    assert vista.casos_positivos_confirmados == 30
    assert vista.tasa_global_positividad == 0.3
    assert vista.tasa_hospitalizacion == 0.1


def test_calcular_vista_kpi_filtrada_recalcula_desde_series() -> None:
    kpis_df = construir_kpis_generales_gold(total_pacientes_atendidos=1000)
    series = construir_series_temporales_gold(
        [
            {
                "pruebas_tomadas": 10,
                "resultados_positivos": 3,
                "resultados_negativos": 7,
                "ingresos_hospitalarios": 1,
            }
        ]
    )
    vista = calcular_vista_kpi(kpis_df, series, sin_filtrar=False)
    assert vista.total_pruebas == 10
    assert vista.casos_positivos_confirmados == 3
    assert round(vista.tasa_global_positividad, 4) == 0.3
    assert round(vista.tasa_hospitalizacion, 4) == round(1 / 3, 4)


def test_calcular_vista_kpi_filtrada_vacia_retorna_ceros() -> None:
    kpis_df = construir_kpis_generales_gold()
    series_vacia = construir_series_temporales_gold([{"fecha": "2021-01-01"}]).iloc[0:0]
    vista = calcular_vista_kpi(kpis_df, series_vacia, sin_filtrar=False)
    assert vista.total_pruebas == 0
    assert vista.casos_positivos_confirmados == 0
    assert vista.tasa_global_positividad == 0.0
    assert vista.tasa_hospitalizacion == 0.0


def test_aplicar_filtro_demografia_sin_seleccion_no_filtra() -> None:
    df = construir_metricas_demografia_gold(
        [{"sexo": "F", "grupo_edad_ui": "18-39"}, {"sexo": "M", "grupo_edad_ui": "60+"}]
    )
    filtrado = aplicar_filtro_demografia(df, _filtro())
    assert len(filtrado) == 2


def test_aplicar_filtro_demografia_sexo_coincidencia_exacta_excluye_otro_indeterminado() -> None:
    df = construir_metricas_demografia_gold(
        [
            {"sexo": "F", "grupo_edad_ui": "18-39"},
            {"sexo": "M", "grupo_edad_ui": "18-39"},
            {"sexo": "OTRO", "grupo_edad_ui": "18-39"},
            {"sexo": "INDETERMINADO", "grupo_edad_ui": "18-39"},
        ]
    )
    filtrado = aplicar_filtro_demografia(df, _filtro(sexos=("F",)))
    assert set(filtrado["sexo"]) == {"F"}


def test_aplicar_filtro_demografia_grupo_edad_ui_filtra() -> None:
    df = construir_metricas_demografia_gold(
        [{"grupo_edad_ui": "<18"}, {"grupo_edad_ui": "18-39"}, {"grupo_edad_ui": "60+"}]
    )
    filtrado = aplicar_filtro_demografia(df, _filtro(grupos_edad_ui=("<18", "60+")))
    assert set(filtrado["grupo_edad_ui"]) == {"<18", "60+"}


def test_calcular_vista_kpi_con_demografia_filtrada_usa_esa_fuente() -> None:
    # US2 Acceptance Scenario 2: filtrar por sexo debe reflejarse en los KPIs, algo
    # que series_temporales (sin dimensión sexo) no puede resolver por sí solo.
    kpis_df = construir_kpis_generales_gold(total_pacientes_atendidos=1000)
    series = construir_series_temporales_gold([{"fecha": "2021-01-01"}])
    demografia_filtrada = construir_metricas_demografia_gold(
        [
            {
                "sexo": "F",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "HOSPITALIZADO",
                "total_casos": 3,
            },
            {
                "sexo": "F",
                "resultado_prueba": "NEGATIVO",
                "estatus_paciente": "AMBULATORIO",
                "total_casos": 7,
            },
        ]
    )
    vista = calcular_vista_kpi(
        kpis_df, series, sin_filtrar=False, demografia_filtrada=demografia_filtrada
    )
    assert vista.total_pruebas == 10
    assert vista.casos_positivos_confirmados == 3
    assert round(vista.tasa_global_positividad, 4) == 0.3
    assert vista.tasa_hospitalizacion == 1.0


def test_calcular_vista_kpi_con_demografia_filtrada_vacia_retorna_ceros() -> None:
    kpis_df = construir_kpis_generales_gold()
    series = construir_series_temporales_gold([{"fecha": "2021-01-01"}])
    demografia_vacia = construir_metricas_demografia_gold([{}]).iloc[0:0]
    vista = calcular_vista_kpi(
        kpis_df, series, sin_filtrar=False, demografia_filtrada=demografia_vacia
    )
    assert vista.total_pruebas == 0
    assert vista.tasa_global_positividad == 0.0


def test_aplicar_filtro_derechohabiencia_sin_seleccion_no_filtra() -> None:
    df = construir_metricas_derechohabiencia_gold(
        [{"derechohabiencia": "IMSS"}, {"derechohabiencia": "ISSSTE"}]
    )
    filtrado = aplicar_filtro_derechohabiencia(df, _filtro())
    assert len(filtrado) == 2


def test_aplicar_filtro_derechohabiencia_coincidencia_exacta() -> None:
    df = construir_metricas_derechohabiencia_gold(
        [
            {"derechohabiencia": "IMSS"},
            {"derechohabiencia": "ISSSTE"},
            {"derechohabiencia": "OTRA"},
        ]
    )
    filtrado = aplicar_filtro_derechohabiencia(df, _filtro(derechohabiencias=("IMSS",)))
    assert set(filtrado["derechohabiencia"]) == {"IMSS"}
