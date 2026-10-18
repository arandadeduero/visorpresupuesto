from budget.common import (
    code_str,
    find_file,
    largest_remainder,
    num,
    sentence_case,
)


def test_code_str_normaliza_numeros_y_textos():
    assert code_str(112.0) == "112"
    assert code_str("300.00") == "300.00"
    assert code_str(None) is None


def test_num_devuelve_none_si_no_es_numero():
    assert num("x") is None
    assert num("#REF!") is None
    assert num(1.234) == 1.23
    assert num(3) == 3.0
    assert num(True) is None


def test_sentence_case_conserva_siglas_y_textos_ya_en_minusculas():
    assert sentence_case("IMPUESTO SOBRE EL IVA") == "Impuesto sobre el IVA"
    assert sentence_case("Sueldos del Grupo C1") == "Sueldos del Grupo C1"


def test_sentence_case_con_un_fragmento_ya_en_minusculas():
    assert sentence_case("TASA DE BASURAS: RECOGIDA Y TRANSPORTE (Ley 7/2022)") == "Tasa de basuras: recogida y transporte (Ley 7/2022)"


def test_largest_remainder_suma_exactamente_100():
    assert largest_remainder([37.84, 33.64, 24.29, 4.22]) == [38, 34, 24, 4]


def test_find_file_localiza_el_excel_por_prefijo():
    assert find_file(2026, "A3").name.startswith("A3")
