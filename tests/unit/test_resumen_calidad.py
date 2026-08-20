from covid_analytics.models import construir_resumen_calidad


def test_construir_resumen_calidad_calcula_porcentaje_huerfanos() -> None:
    resumen = construir_resumen_calidad(
        filas_leidas_bronze_seguimiento=10,
        filas_leidas_bronze_nominal=8,
        registros_hasheados=18,
        cruces_exitosos=3,
        registros_huerfanos=1,
        correcciones_columnas_intercambiadas=2,
        colisiones_llave_sintetica=0,
    )

    assert resumen.porcentaje_huerfanos == 0.25
    assert resumen.filas_leidas_bronze_seguimiento == 10
    campos = type(resumen).model_fields
    assert all(getattr(resumen, campo) >= 0 for campo in campos if campo != "timestamp_ejecucion")


def test_construir_resumen_calidad_sin_cruces_ni_huerfanos_no_divide_entre_cero() -> None:
    resumen = construir_resumen_calidad(
        filas_leidas_bronze_seguimiento=0,
        filas_leidas_bronze_nominal=0,
        registros_hasheados=0,
        cruces_exitosos=0,
        registros_huerfanos=0,
        correcciones_columnas_intercambiadas=0,
        colisiones_llave_sintetica=0,
    )

    assert resumen.porcentaje_huerfanos == 0.0


def test_construir_resumen_calidad_ninguna_metrica_es_nula() -> None:
    # SC-003: ninguna métrica en nulo.
    resumen = construir_resumen_calidad(
        filas_leidas_bronze_seguimiento=1,
        filas_leidas_bronze_nominal=1,
        registros_hasheados=2,
        cruces_exitosos=0,
        registros_huerfanos=2,
        correcciones_columnas_intercambiadas=0,
        colisiones_llave_sintetica=0,
    )

    for valor in resumen.model_dump().values():
        assert valor is not None
