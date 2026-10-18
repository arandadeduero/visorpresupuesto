import pytest

from budget.gastos import parse_gastos


@pytest.fixture(scope="module")
def d():
    return parse_gastos(2026)


def test_totales_por_capitulo(d):
    esperado = {1: 15616598.5, 2: 21623640, 3: 184000, 4: 1929680, 5: 50000, 6: 24206942.85, 7: 120000, 8: 15000, 9: 535000}
    assert {c["cap"]: c["y2026"] for c in d["capitulos"]} == pytest.approx(esperado, abs=0.01)


def test_las_partidas_suman_el_total_de_cada_capitulo(d):
    for c in d["capitulos"]:
        suma = sum(p["y2026"] or 0 for p in d["partidas"] if p["cap"] == c["cap"])
        assert suma == pytest.approx(c["y2026"], abs=1), f"capítulo {c['cap']}"


def test_personal_solo_agrupado_por_programa(d):
    personal = [p for p in d["partidas"] if p["cap"] == 1]
    assert all(p["codigo"] is None and p["nombre"] == "Gastos de personal" for p in personal)
    por_programa = {p["programa"]: p["y2026"] for p in personal}
    assert por_programa["1300"] == 177175
    assert por_programa["1320"] == 2494600
    assert len(personal) == len(por_programa)


def test_inversiones_llegan_a_la_partida(d):
    seg = {p["codigo"]: p["y2026"] for p in d["partidas"] if p["cap"] == 6 and p["programa"] == "1320"}
    assert seg == {"622": 110000, "624": 45000}


def test_programas_con_nombre_y_area(d):
    assert all(p["nombre"] for p in d["programas"])
    assert {p["area"] for p in d["programas"]} <= {0, 1, 2, 3, 4, 9}
    assert {a["area"] for a in d["areas"]} == {p["area"] for p in d["programas"]}
    seg = next(p for p in d["programas"] if p["codigo"] == "1320")
    assert seg["area"] == 1 and seg["nombre"] == "Seguridad"
    # personal 2.494.600 + bienes y servicios 244.100 + inversiones 155.000
    assert seg["y2026"] == 2494600 + 244100 + 155000
    assert next(p for p in d["programas"] if p["codigo"] == "0110")["area"] == 0


def test_los_programas_suman_el_total(d):
    assert sum(p["y2026"] for p in d["programas"]) == pytest.approx(64280861.35, abs=1)


def test_politicas_de_gasto_con_nombre_llano(d):
    politicas = {p["codigo"]: p for p in d["politicas"]}
    assert politicas["13"]["nombre"] == "Seguridad y movilidad ciudadana"
    assert politicas["01"]["nombre"] == "Deuda pública" and politicas["01"]["area"] == 0
    assert politicas["34"]["nombre"] == "Deporte" and politicas["33"]["nombre"] == "Cultura"
    assert politicas["92"]["area"] == 9
    assert sum(p["y2026"] for p in politicas.values()) == pytest.approx(64280861.35, abs=1)


def test_cada_programa_cuelga_de_una_politica_conocida(d):
    codigos = {p["codigo"] for p in d["politicas"]}
    for p in d["programas"]:
        assert p["politica"] == p["codigo"][:2]
        assert p["politica"] in codigos
    seg = next(p for p in d["politicas"] if p["codigo"] == "13")
    assert seg["y2026"] == pytest.approx(sum(p["y2026"] for p in d["programas"] if p["politica"] == "13"), abs=0.01)
