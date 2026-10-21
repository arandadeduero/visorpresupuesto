import copy
import json

import pytest

import convert as conv

NOMBRES = ["resumen", "ingresos", "gastos", "inversiones", "subvenciones", "deuda"]
ANIOS = [2024, 2025, 2026]


@pytest.fixture(scope="module")
def generado(tmp_path_factory):
    out = tmp_path_factory.mktemp("data")
    avisos = {a: conv.convert(a, out) for a in ANIOS}
    return out, avisos


@pytest.mark.parametrize("anio", ANIOS)
def test_escribe_los_seis_json_de_cada_anio(generado, anio):
    out, _ = generado
    for n in NOMBRES:
        datos = json.loads((out / str(anio) / f"{n}.json").read_text(encoding="utf-8"))
        assert datos["anio"] == anio


def test_el_indice_lista_los_tres_anios_ordenados_y_el_ultimo_es_el_por_defecto(generado):
    out, _ = generado
    assert json.loads((out / "index.json").read_text(encoding="utf-8")) == {
        "anios": [{"anio": a, "tipo": "aprobado"} for a in ANIOS],
        "ultimo": 2026,
    }


@pytest.mark.parametrize("anio", ANIOS)
def test_los_datos_de_cada_anio_cuadran_sin_avisos(generado, anio):
    assert generado[1][anio] == []


@pytest.mark.parametrize("anio", ANIOS)
def test_los_json_no_llevan_restos_de_excel(generado, anio):
    out, _ = generado
    for n in NOMBRES:
        texto = (out / str(anio) / f"{n}.json").read_text(encoding="utf-8")
        assert "#REF" not in texto and "#DIV" not in texto and "NaN" not in texto and "Loading" not in texto, f"{anio}/{n}"


def test_convertir_dos_veces_no_duplica_el_anio(tmp_path):
    conv.convert(2025, tmp_path)
    conv.convert(2025, tmp_path)
    assert len(json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))["anios"]) == 1


def test_el_indice_se_ordena_aunque_se_conviertan_los_anios_desordenados(tmp_path):
    for a in (2026, 2024, 2025):
        conv.convert(a, tmp_path)
    indice = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert [a["anio"] for a in indice["anios"]] == [2024, 2025, 2026] and indice["ultimo"] == 2026


def _datos(anio):
    return {n: getattr(__import__(f"budget.{n}", fromlist=["x"]), f"parse_{n}")(anio) for n in NOMBRES}


@pytest.mark.parametrize("anio", ANIOS)
def test_check_totals_avisa_de_descuadres(anio):
    data = _datos(anio)
    assert conv.check_totals(data, anio) == []
    roto = copy.deepcopy(data)
    next(c for c in roto["gastos"]["capitulos"] if c["cap"] == 2)["actual"] += 500
    avisos = conv.check_totals(roto, anio)
    assert avisos and all("capítulo 2" in a for a in avisos)


@pytest.mark.parametrize("anio", ANIOS)
def test_check_totals_avisa_si_las_partidas_no_suman_el_capitulo(anio):
    roto = copy.deepcopy(_datos(anio))
    roto["gastos"]["partidas"][-1]["actual"] += 700
    avisos = conv.check_totals(roto, anio)
    assert len(avisos) == 1 and "partidas" in avisos[0] and "capítulo" in avisos[0]


@pytest.mark.parametrize("anio", ANIOS)
def test_check_totals_avisa_si_los_proyectos_no_suman_las_inversiones(anio):
    roto = copy.deepcopy(_datos(anio))
    roto["inversiones"]["programas"][0]["proyectos"][0]["importe"] += 300
    roto["inversiones"]["programas"][0]["total"] += 300
    avisos = conv.check_totals(roto, anio)
    assert len(avisos) == 1 and "proyectos" in avisos[0]


@pytest.mark.parametrize("anio", ANIOS)
def test_check_totals_avisa_si_los_conceptos_de_ingresos_no_suman_el_capitulo(anio):
    roto = copy.deepcopy(_datos(anio))
    roto["ingresos"]["capitulos"][0]["conceptos"][0]["actual"] += 900
    avisos = conv.check_totals(roto, anio)
    assert len(avisos) == 1 and "conceptos" in avisos[0]


@pytest.mark.parametrize("anio", ANIOS)
def test_check_totals_avisa_si_la_amortizacion_no_cuadra_con_los_prestamos(anio):
    roto = copy.deepcopy(_datos(anio))
    roto["deuda"]["carga"]["amortizacion"] += 5000
    avisos = conv.check_totals(roto, anio)
    assert len(avisos) == 1 and "amortización" in avisos[0]


@pytest.mark.parametrize("anio", [2024, 2026])
def test_ingresos_y_gastos_totales_coinciden_y_un_descuadre_avisa(anio):
    data = _datos(anio)
    assert data["resumen"]["totalIngresos"] == pytest.approx(data["resumen"]["totalGastos"], abs=0.01)
    roto = copy.deepcopy(data)
    roto["resumen"]["totalIngresos"] += 1000
    assert any("ingresos y gastos totales" in a for a in conv.check_totals(roto, anio))


def test_en_2025_el_excel_trae_250000_euros_mas_de_ingresos_que_de_gastos_y_es_una_nota_conocida():
    data = _datos(2025)
    r = data["resumen"]
    assert r["totalIngresos"] - r["totalGastos"] == pytest.approx(250000, abs=0.01)
    assert conv.check_totals(data, 2025) == []  # diferencia esperada: no es un aviso
    notas = conv.notas_conocidas(data, 2025)
    assert len(notas) == 1 and "250.000" in notas[0]
    # pero si la diferencia cambia, sí avisa
    roto = copy.deepcopy(data)
    roto["resumen"]["totalIngresos"] += 1000
    assert any("ingresos y gastos totales" in a for a in conv.check_totals(roto, 2025))
    assert conv.notas_conocidas(_datos(2026), 2026) == []
