import hashlib

from covid_analytics.ingestion.pii import generar_hash_pii, normalizar_nombre


def test_normalizar_nombre_quita_acentos_y_mayusculas() -> None:
    assert normalizar_nombre("María José Pérez") == "MARIA JOSE PEREZ"


def test_normalizar_nombre_colapsa_espacios() -> None:
    assert normalizar_nombre("  Juan   Perez  ") == "JUAN PEREZ"


def test_normalizar_nombre_conserva_ene() -> None:
    assert normalizar_nombre("Muñoz") == "MUÑOZ"


def test_generar_hash_pii_es_determinista() -> None:
    h1 = generar_hash_pii("Juan Perez", "123", "sal-test")
    h2 = generar_hash_pii("juan   perez", "123", "sal-test")
    assert h1 == h2
    assert len(h1) == 64


def test_generar_hash_pii_formula_explicita() -> None:
    esperado = hashlib.sha256(("JUAN PEREZ" + "123" + "sal-test").encode("utf-8")).hexdigest()
    assert generar_hash_pii("Juan Perez", "123", "sal-test") == esperado


def test_generar_hash_pii_folio_ausente_no_bloquea_ingestion() -> None:
    # Edge Case (spec.md): folio nulo/inválido -> máscara determinista, no debe lanzar.
    h = generar_hash_pii("Juan Perez", None, "sal-test")
    assert len(h) == 64
    esperado = hashlib.sha256(("JUAN PEREZ" + "" + "sal-test").encode("utf-8")).hexdigest()
    assert h == esperado
