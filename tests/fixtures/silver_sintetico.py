"""Generador de DataFrames Silver 100% sintéticos para pruebas de la capa Gold."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

_COLUMNAS_FECHA = [
    "fecha_notificacion",
    "fecha_toma_muestra",
    "fecha_resultado",
    "fecha_ingreso_hospital",
]

_DEFAULTS: dict[str, Any] = {
    "paciente_id": "0" * 64,
    "edad": 30.0,
    "sexo": "F",
    "municipio_residencia": "OTROS",
    "derechohabiencia": "NINGUNO",
    "fecha_notificacion": None,
    "fecha_toma_muestra": None,
    "fecha_resultado": None,
    "resultado_prueba": "PENDIENTE",
    "estatus_paciente": "AMBULATORIO",
    "hospital": None,
    "fecha_ingreso_hospital": None,
    "es_registro_unificado": False,
    "dias_entre_notificacion_e_ingreso": None,
}


def construir_caso_silver(**overrides: Any) -> dict[str, Any]:
    """Construye un registro Silver sintético con valores por defecto seguros."""
    caso = dict(_DEFAULTS)
    caso.update(overrides)
    return caso


def construir_silver_sintetico(filas: list[dict[str, Any]]) -> pd.DataFrame:
    """Construye un DataFrame Silver sintético a partir de overrides por fila.

    Cada elemento de `filas` es un dict de overrides sobre `construir_caso_silver`,
    permitiendo declarar solo los campos relevantes para cada caso de prueba.
    """
    registros = [construir_caso_silver(**fila) for fila in filas]
    df = pd.DataFrame.from_records(registros, columns=list(_DEFAULTS.keys()))
    for columna in _COLUMNAS_FECHA:
        df[columna] = pd.to_datetime(df[columna])
    return df


def generar_dataset_variado(n_dias: int = 30, casos_por_dia: int = 4) -> pd.DataFrame:
    """Genera un dataset sintético con combinaciones variadas de edad, sexo,
    resultado, estatus, municipio y fechas a lo largo de `n_dias`, incluyendo
    casos con `edad` sin dato y algunos con fechas invertidas (FR-004a).
    """
    edades = [0.5, 5.0, 15.0, 20.0, 28.0, 33.0, 38.0, 43.0, 48.0, 53.0, 58.0, 63.0, 70.0, -1.0]
    sexos = ["F", "M", "OTRO", "INDETERMINADO"]
    resultados = ["POSITIVO", "NEGATIVO", "PENDIENTE", "NO_CONCLUYENTE"]
    estatus = ["AMBULATORIO", "HOSPITALIZADO", "DEFUNCION"]
    municipios = ["NEZAHUALCOYOTL", "CHIMALHUACAN", "LA PAZ", "ECATEPEC", "OTROS"]

    filas: list[dict[str, Any]] = []
    inicio = datetime(2021, 1, 1)
    for dia in range(n_dias):
        fecha_base = inicio + pd.Timedelta(days=dia)
        for i in range(casos_por_dia):
            idx = dia * casos_por_dia + i
            estatus_actual = estatus[idx % len(estatus)]
            fecha_toma = fecha_base
            fecha_resultado = fecha_base + pd.Timedelta(days=2)
            if idx % 17 == 0:  # inyecta anomalías de fechas invertidas (FR-004a)
                fecha_toma, fecha_resultado = fecha_resultado, fecha_toma
            es_hospitalizado = estatus_actual == "HOSPITALIZADO"
            filas.append(
                construir_caso_silver(
                    paciente_id=f"{idx:064d}",
                    edad=edades[idx % len(edades)],
                    sexo=sexos[idx % len(sexos)],
                    municipio_residencia=municipios[idx % len(municipios)],
                    resultado_prueba=resultados[idx % len(resultados)],
                    estatus_paciente=estatus_actual,
                    fecha_notificacion=fecha_base,
                    fecha_toma_muestra=fecha_toma,
                    fecha_resultado=fecha_resultado,
                    fecha_ingreso_hospital=fecha_base + pd.Timedelta(days=1)
                    if es_hospitalizado
                    else None,
                    es_registro_unificado=es_hospitalizado,
                    dias_entre_notificacion_e_ingreso=1 if es_hospitalizado else None,
                )
            )
    return construir_silver_sintetico(filas)
