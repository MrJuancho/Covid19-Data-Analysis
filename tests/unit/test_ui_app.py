import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tests.fixtures.gold_sintetico import escribir_gold_sintetico

APP_PATH = str(Path(__file__).resolve().parents[2] / "src" / "covid_analytics" / "ui" / "app.py")

_ETIQUETAS_KPI = {
    "Total Pruebas",
    "Casos Positivos Confirmados",
    "Tasa Global de Positividad",
    "Tasa de Hospitalización",
}


def _run_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **kwargs: object) -> AppTest:
    escribir_gold_sintetico(tmp_path, **kwargs)  # type: ignore[arg-type]
    monkeypatch.chdir(tmp_path)
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    return at


def _figura_json(tab: object, indice: int = 0) -> dict:  # type: ignore[type-arg]
    """Decodifica el spec JSON de la n-ésima figura Plotly de una pestaña de AppTest."""
    elemento = tab.get("plotly_chart")[indice]  # type: ignore[attr-defined]
    spec: dict = json.loads(elemento.proto.spec)
    return spec


def test_app_sin_artefactos_gold_muestra_estado_inicial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    assert not at.exception
    assert any("pipeline" in i.value.lower() for i in at.info)
    assert len(at.tabs) == 0


def test_kpis_y_pestana_1_renderizan_sin_filtro(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        series=[
            {"fecha": "2021-01-01", "resultados_positivos": 2, "resultados_negativos": 3},
            {"fecha": "2021-01-02", "resultados_positivos": 1, "resultados_negativos": 4},
            {"fecha": "2021-01-03", "resultados_positivos": 3, "resultados_negativos": 2},
        ],
        kpis={"total_pacientes_atendidos": 15, "total_positivos": 6},
    )
    assert not at.exception
    etiquetas = {m.label for m in at.metric}
    assert _ETIQUETAS_KPI <= etiquetas

    valores = {m.label: m.value for m in at.metric}
    assert valores["Total Pruebas"] == "15"
    assert valores["Casos Positivos Confirmados"] == "6"

    assert len(at.tabs) == 5
    assert len(at.tabs[0].get("plotly_chart")) >= 1


def test_cambiar_rango_de_fechas_actualiza_kpis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        series=[
            {
                "fecha": "2021-01-01",
                "resultados_positivos": 2,
                "resultados_negativos": 3,
                "pruebas_tomadas": 5,
            },
            {
                "fecha": "2021-01-02",
                "resultados_positivos": 1,
                "resultados_negativos": 4,
                "pruebas_tomadas": 5,
            },
            {
                "fecha": "2021-01-03",
                "resultados_positivos": 3,
                "resultados_negativos": 2,
                "pruebas_tomadas": 5,
            },
        ],
        kpis={"total_pacientes_atendidos": 15, "total_positivos": 6},
    )
    valores_iniciales = {m.label: m.value for m in at.metric}
    assert valores_iniciales["Total Pruebas"] == "15"

    at.sidebar.slider(key="filtro_fechas").set_value((date(2021, 1, 1), date(2021, 1, 1)))
    at.run(timeout=30)
    assert not at.exception

    valores_filtrados = {m.label: m.value for m in at.metric}
    assert valores_filtrados["Total Pruebas"] == "5"
    assert valores_filtrados["Casos Positivos Confirmados"] == "2"


def test_pestana_1_curva_excluye_dias_sin_casos_confirmados(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        series=[
            {"fecha": "2021-01-01", "resultados_positivos": 5},
            {"fecha": "2021-01-02", "resultados_positivos": 0},
            {"fecha": "2021-01-03", "resultados_positivos": 3},
        ],
    )
    assert not at.exception
    figura = _figura_json(at.tabs[0])
    traza_positivos = next(t for t in figura["data"] if t.get("name") == "resultados_positivos")
    assert len(traza_positivos["x"]) == 2
    assert "2021-01-02T00:00:00.000000" not in traza_positivos["x"]


def test_pestana_1_curva_todos_los_dias_sin_casos_muestra_aviso(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        series=[
            {"fecha": "2021-01-01", "resultados_positivos": 0},
            {"fecha": "2021-01-02", "resultados_positivos": 0},
        ],
    )
    assert not at.exception
    assert len(at.tabs[0].get("plotly_chart")) == 0
    assert len(at.tabs[0].info) >= 1


def test_pestana_2_renderiza_piramide_sin_filtro(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        demografia=[
            {"sexo": "F", "grupo_edad_ui": "18-39", "resultado_prueba": "POSITIVO"},
            {"sexo": "M", "grupo_edad_ui": "40-59", "resultado_prueba": "NEGATIVO"},
        ],
    )
    assert not at.exception
    pestana_demografia = at.tabs[1]
    assert len(pestana_demografia.get("plotly_chart")) >= 2  # pirámide + barras positividad


def test_pestana_2_filtro_sexo_femenino_actualiza_kpis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        demografia=[
            {
                "sexo": "F",
                "grupo_edad_ui": "18-39",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "HOSPITALIZADO",
                "total_casos": 4,
            },
            {
                "sexo": "F",
                "grupo_edad_ui": "18-39",
                "resultado_prueba": "NEGATIVO",
                "estatus_paciente": "AMBULATORIO",
                "total_casos": 6,
            },
            {
                "sexo": "M",
                "grupo_edad_ui": "40-59",
                "resultado_prueba": "POSITIVO",
                "estatus_paciente": "AMBULATORIO",
                "total_casos": 100,
            },
        ],
        kpis={"total_pacientes_atendidos": 110, "total_positivos": 101},
    )
    at.sidebar.multiselect(key="filtro_sexo").set_value(["FEMENINO"])
    at.run(timeout=30)
    assert not at.exception

    valores = {m.label: m.value for m in at.metric}
    assert valores["Total Pruebas"] == "10"
    assert valores["Casos Positivos Confirmados"] == "4"


def test_pestana_3_renderiza_mapa_de_municipios_conocidos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        geografia=[
            {"municipio_residencia": "ECATEPEC", "total_casos": 20},
            {"municipio_residencia": "NEZAHUALCOYOTL", "total_casos": 15},
        ],
    )
    assert not at.exception
    assert len(at.tabs[2].get("plotly_chart")) >= 1


def test_pestana_3_mapa_altura_prominente_y_margenes_ajustados(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        geografia=[{"municipio_residencia": "ECATEPEC", "total_casos": 20}],
    )
    assert not at.exception
    figura = _figura_json(at.tabs[2])
    assert figura["layout"].get("height") in (650, 700)
    margin = figura["layout"].get("margin", {})
    assert margin.get("l") == 10
    assert margin.get("r") == 10
    assert margin.get("t") == 30
    assert margin.get("b") == 10


def test_pestana_4_renderiza_barras_agrupadas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        derechohabiencia=[
            {"derechohabiencia": "IMSS", "resultado_prueba": "POSITIVO"},
            {"derechohabiencia": "ISSSTE", "resultado_prueba": "NEGATIVO"},
        ],
    )
    assert not at.exception
    assert len(at.tabs[3].get("plotly_chart")) >= 1
    figura = _figura_json(at.tabs[3])
    assert figura["layout"].get("barmode") == "group"


def test_pestana_4_excluye_categorias_sin_valor_analitico(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        derechohabiencia=[
            {"derechohabiencia": "IMSS", "resultado_prueba": "POSITIVO", "total_casos": 10},
            {"derechohabiencia": "ISSSTE", "resultado_prueba": "NEGATIVO", "total_casos": 5},
            {"derechohabiencia": "OTRA", "resultado_prueba": "POSITIVO", "total_casos": 2},
            {"derechohabiencia": "IMSS", "resultado_prueba": "NO_ESPECIFICADO", "total_casos": 1},
        ],
    )
    assert not at.exception
    figura = _figura_json(at.tabs[3])
    categorias_x = {x for traza in figura["data"] for x in traza.get("x", [])}
    assert "OTRA" not in categorias_x
    nombres_series = {traza.get("name") for traza in figura["data"]}
    assert "NO_ESPECIFICADO" not in nombres_series


def test_pestana_4_degrada_sola_cuando_falta_el_archivo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        series=[{"fecha": "2021-01-01"}],
        incluir_derechohabiencia=False,
    )
    assert not at.exception
    # El resto del tablero sigue funcionando (degradación por pestaña, FR-013).
    assert len(at.metric) >= 1
    assert len(at.tabs[0].get("plotly_chart")) >= 1
    assert any("no disponible" in i.value.lower() for i in at.tabs[3].info)


def test_rendimiento_carga_inicial_y_refiltrado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Proxy de SC-003 (<5s carga inicial) y SC-002 (<2s al cambiar un filtro),
    sobre un volumen sintético del orden de magnitud típico del hospital."""
    inicio = datetime(2021, 1, 1)
    dias = 180
    series = [
        {
            "fecha": (inicio + timedelta(days=i)).date().isoformat(),
            "resultados_positivos": 10,
            "resultados_negativos": 20,
            "pruebas_tomadas": 30,
        }
        for i in range(dias)
    ]
    demografia = [
        {"grupo_edad_ui": g, "sexo": s, "resultado_prueba": r, "total_casos": 50}
        for g in ("<18", "18-39", "40-59", "60+")
        for s in ("F", "M")
        for r in ("POSITIVO", "NEGATIVO")
    ]

    inicio_carga = time.perf_counter()
    at = _run_app(tmp_path, monkeypatch, series=series, demografia=demografia)
    duracion_carga = time.perf_counter() - inicio_carga
    assert not at.exception
    assert duracion_carga < 5.0, f"Carga inicial tomó {duracion_carga:.2f}s (SC-003: <5s)"

    inicio_filtro = time.perf_counter()
    at.sidebar.slider(key="filtro_fechas").set_value(
        (inicio.date(), (inicio + timedelta(days=7)).date())
    )
    at.run(timeout=30)
    duracion_filtro = time.perf_counter() - inicio_filtro
    assert not at.exception
    assert duracion_filtro < 2.0, f"Refiltrado tomó {duracion_filtro:.2f}s (SC-002: <2s)"


def test_pestana_5_muestra_reporte_de_calidad(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        reporte_calidad={"fechas_anomalas_fuera_ventana": 3, "cruces_exitosos": 7},
    )
    assert not at.exception
    pestana_calidad = at.tabs[4]
    assert len(pestana_calidad.json) == 1
    contenido = json.loads(pestana_calidad.json[0].value)
    assert contenido["fechas_anomalas_fuera_ventana"] == 3
    assert contenido["cruces_exitosos"] == 7


def test_pestana_5_reporte_ausente_muestra_mensaje_explicativo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        series=[{"fecha": "2021-01-01"}],
        incluir_reporte_calidad=False,
    )
    assert not at.exception
    assert any("no disponible" in i.value.lower() for i in at.tabs[4].info)


def test_pestana_3_municipio_sin_geometria_no_rompe_la_vista(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = _run_app(
        tmp_path,
        monkeypatch,
        geografia=[
            {"municipio_residencia": "ECATEPEC", "total_casos": 20},
            # "TOLUCA" no existe en el shapefile mínimo de prueba (solo tiene
            # Ecatepec y Nezahualcóyotl) -> debe omitirse sin romper la vista.
            {"municipio_residencia": "TOLUCA", "total_casos": 5},
        ],
    )
    assert not at.exception
    assert len(at.tabs[2].get("plotly_chart")) >= 1
