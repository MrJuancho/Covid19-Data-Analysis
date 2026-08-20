from covid_analytics.cleaning.demografia import unificar_demografia


def test_unificar_demografia_numerico_simple() -> None:
    assert unificar_demografia("34", "F") == (34.0, "F")


def test_unificar_demografia_recien_nacido() -> None:
    assert unificar_demografia("RN", "M") == (0.0, "M")


def test_unificar_demografia_meses() -> None:
    assert unificar_demografia("3M", "F") == (0.0, "F")


def test_unificar_demografia_texto_con_numero() -> None:
    assert unificar_demografia("años: 4", "M") == (4.0, "M")


def test_unificar_demografia_ambos_nulos_usa_sentinels() -> None:
    # Edge Case (spec.md): EDAD|F y EDAD|M ambos nulos -> edad -1.0, sexo INDETERMINADO
    assert unificar_demografia(None, None) == (-1.0, "INDETERMINADO")


def test_unificar_demografia_corrige_intercambio_sexo_edad() -> None:
    # El valor de edad terminó en la columna de sexo y viceversa (docs/audit_legacy.md).
    assert unificar_demografia("F", "34") == (34.0, "F")


def test_unificar_demografia_sexo_desconocido_es_otro() -> None:
    assert unificar_demografia("50", "X") == (50.0, "OTRO")
