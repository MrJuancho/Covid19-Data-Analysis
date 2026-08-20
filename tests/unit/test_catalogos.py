from covid_analytics.cleaning.catalogos import (
    estandarizar_estatus_paciente,
    estandarizar_municipio,
    estandarizar_resultado_prueba,
)


def test_estandarizar_municipio_mapeo_directo() -> None:
    assert estandarizar_municipio("GAM") == "GUSTAVO A. MADERO"
    assert estandarizar_municipio("TLALNEPANTLA DE BAZ") == "TLALNEPANTLA"


def test_estandarizar_municipio_no_reconocido_es_otros() -> None:
    assert estandarizar_municipio("MUNICIPIO INEXISTENTE XYZ") == "OTROS"
    assert estandarizar_municipio(None) == "OTROS"


def test_estandarizar_resultado_prueba_positivo() -> None:
    assert estandarizar_resultado_prueba("POSITIVO") == "POSITIVO"
    assert estandarizar_resultado_prueba("positivo") == "POSITIVO"
    assert estandarizar_resultado_prueba("REACTIVO") == "POSITIVO"


def test_estandarizar_resultado_prueba_negativo() -> None:
    assert estandarizar_resultado_prueba("NEGATIVO") == "NEGATIVO"


def test_estandarizar_resultado_prueba_pendiente_incluye_no_se_tomo() -> None:
    # FR-009: NO SE TOMO / NO SE TOMÓ / PEDIENTE deben mapear a PENDIENTE.
    assert estandarizar_resultado_prueba("PENDIENTE") == "PENDIENTE"
    assert estandarizar_resultado_prueba("NO SE TOMO") == "PENDIENTE"
    assert estandarizar_resultado_prueba("NO SE TOMÓ") == "PENDIENTE"
    assert estandarizar_resultado_prueba("PEDIENTE") == "PENDIENTE"


def test_estandarizar_resultado_prueba_no_concluyente_incluye_rechazo() -> None:
    # FR-009: RECHAZO / RECHAZADA deben mapear a NO_CONCLUYENTE.
    assert estandarizar_resultado_prueba("INDETERMINADO") == "NO_CONCLUYENTE"
    assert estandarizar_resultado_prueba("RECHAZO") == "NO_CONCLUYENTE"
    assert estandarizar_resultado_prueba("RECHAZADA") == "NO_CONCLUYENTE"


def test_estandarizar_resultado_prueba_fallback_no_especificado() -> None:
    assert estandarizar_resultado_prueba("VALOR-RARO-XYZ") == "NO_ESPECIFICADO"
    assert estandarizar_resultado_prueba(None) == "NO_ESPECIFICADO"


def test_estandarizar_estatus_paciente_ambulatorio_incluye_alta() -> None:
    assert estandarizar_estatus_paciente("AMBULATORIO") == "AMBULATORIO"
    assert estandarizar_estatus_paciente("ALTA") == "AMBULATORIO"
    assert estandarizar_estatus_paciente("ESTABLE") == "AMBULATORIO"


def test_estandarizar_estatus_paciente_hospitalizado() -> None:
    assert estandarizar_estatus_paciente("HOSPITALIZADO") == "HOSPITALIZADO"
    assert estandarizar_estatus_paciente("URGENCIAS") == "HOSPITALIZADO"


def test_estandarizar_estatus_paciente_defuncion_variantes_acento() -> None:
    assert estandarizar_estatus_paciente("DEFUNCION") == "DEFUNCION"
    assert estandarizar_estatus_paciente("DEFUNCIÓN") == "DEFUNCION"


def test_estandarizar_estatus_paciente_fallback_no_especificado() -> None:
    assert estandarizar_estatus_paciente("VALOR-RARO-XYZ") == "NO_ESPECIFICADO"
    assert estandarizar_estatus_paciente(None) == "NO_ESPECIFICADO"
