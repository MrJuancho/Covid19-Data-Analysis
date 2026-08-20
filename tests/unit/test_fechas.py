from datetime import datetime

from covid_analytics.cleaning.fechas import (
    FECHA_MAX_VALIDA,
    FECHA_MIN_VALIDA,
    normalizar_typo_anio,
    parse_fecha_con_telemetria,
    parse_fecha_polimorfica,
)


def test_parse_fecha_polimorfica_datetime_nativo() -> None:
    dt = datetime(2020, 3, 24)
    assert parse_fecha_polimorfica(dt) == dt


def test_parse_fecha_polimorfica_serial_excel() -> None:
    # 43914 == 2020-03-24 en el origen de fechas de Excel (1899-12-30).
    resultado = parse_fecha_polimorfica(43914)
    assert resultado == datetime(2020, 3, 24)


def test_parse_fecha_polimorfica_string_con_texto_adicional() -> None:
    resultado = parse_fecha_polimorfica("24/03/2020  H. ZUMPANGO")
    assert resultado == datetime(2020, 3, 24)


def test_parse_fecha_polimorfica_string_estructurado_dayfirst() -> None:
    resultado = parse_fecha_polimorfica("18/03/2020")
    assert resultado == datetime(2020, 3, 18)


def test_parse_fecha_polimorfica_texto_no_fecha_retorna_none() -> None:
    assert parse_fecha_polimorfica("PENDIENTE") is None


def test_parse_fecha_polimorfica_none_retorna_none() -> None:
    assert parse_fecha_polimorfica(None) is None


def test_ventana_epidemiologica_limites() -> None:
    assert FECHA_MIN_VALIDA == datetime(2020, 1, 1).date()
    assert FECHA_MAX_VALIDA == datetime(2023, 12, 31).date()


def test_normalizar_typo_anio_corrige_typos_conocidos() -> None:
    assert normalizar_typo_anio("0202-05-15") == "2020-05-15"
    assert normalizar_typo_anio("2920-05-15") == "2020-05-15"
    assert normalizar_typo_anio("15/05/2020") == "15/05/2020"


def test_parse_fecha_polimorfica_corrige_typo_de_anio_antes_de_parsear() -> None:
    resultado = parse_fecha_polimorfica("0202-05-15")
    assert resultado == datetime(2020, 5, 15)


def test_parse_fecha_polimorfica_descarta_fecha_fuera_de_ventana_sin_typo_conocido() -> None:
    # Año "0208" no está en la tabla de typos conocidos, pero igual queda
    # fuera de la ventana epidemiológica tras el parseo -> se descarta.
    assert parse_fecha_polimorfica("0208-05-15") is None


def test_parse_fecha_polimorfica_rechaza_datetime_nativo_fuera_de_ventana() -> None:
    assert parse_fecha_polimorfica(datetime(2019, 12, 31)) is None
    assert parse_fecha_polimorfica(datetime(2024, 1, 1)) is None


def test_parse_fecha_polimorfica_acepta_limites_inclusive_de_la_ventana() -> None:
    assert parse_fecha_polimorfica(datetime(2020, 1, 1)) == datetime(2020, 1, 1)
    assert parse_fecha_polimorfica(datetime(2023, 12, 31)) == datetime(2023, 12, 31)


def test_parse_fecha_con_telemetria_marca_anomalia_fuera_de_ventana() -> None:
    # "0208" no está en la tabla de typos conocidos: parsea estructuralmente
    # pero queda fuera de la ventana -> se telemetra como anomalía real.
    fecha, es_anomalia = parse_fecha_con_telemetria("0208-05-15")
    assert fecha is None
    assert es_anomalia is True


def test_parse_fecha_con_telemetria_no_marca_anomalia_para_dato_ausente() -> None:
    fecha, es_anomalia = parse_fecha_con_telemetria(None)
    assert fecha is None
    assert es_anomalia is False


def test_parse_fecha_con_telemetria_no_marca_anomalia_para_fecha_valida() -> None:
    fecha, es_anomalia = parse_fecha_con_telemetria("18/03/2020")
    assert fecha == datetime(2020, 3, 18)
    assert es_anomalia is False


def test_parse_fecha_polimorfica_corrige_anio_2022_posterior_a_enero() -> None:
    # El dataset fuente se gestionó solo hasta enero/2022: cualquier fecha con
    # año 2022 en meses posteriores es un typo de captura del año real 2020
    # (mismo mes/día), confirmado por +300 registros reales en sep-oct/2022
    # sin ningún registro en enero/2022.
    assert parse_fecha_polimorfica("18/09/2022") == datetime(2020, 9, 18)
    assert parse_fecha_polimorfica("05/10/2022") == datetime(2020, 10, 5)


def test_parse_fecha_polimorfica_corrige_anio_2022_datetime_nativo() -> None:
    # La corrección aplica tras el parseo (por año), no como substring de
    # texto, para cubrir también datetimes nativos y seriales de Excel.
    assert parse_fecha_polimorfica(datetime(2022, 10, 5)) == datetime(2020, 10, 5)


def test_parse_fecha_polimorfica_preserva_enero_2022_como_valido() -> None:
    # Enero/2022 es el límite real de gestión del dataset: no se corrige.
    assert parse_fecha_polimorfica("15/01/2022") == datetime(2022, 1, 15)


def test_parse_fecha_con_telemetria_no_marca_anomalia_para_typo_2022() -> None:
    fecha, es_anomalia = parse_fecha_con_telemetria("18/09/2022")
    assert fecha == datetime(2020, 9, 18)
    assert es_anomalia is False
