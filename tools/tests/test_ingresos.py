import pytest

from budget.ingresos import parse_ingresos


@pytest.fixture(scope="module")
def d():
    return parse_ingresos(2026)


def cap(d, n):
    return next(c for c in d["capitulos"] if c["cap"] == n)


def test_nueve_capitulos_con_totales(d):
    assert [c["cap"] for c in d["capitulos"]] == list(range(1, 10))
    c1 = cap(d, 1)
    assert (c1["y2026"], c1["y2025"], c1["y2024"]) == (16600000, 15820000, 14678000)
    assert cap(d, 9)["y2026"] == 20161623.64
    assert c1["corto"].startswith("Impuestos directos")


def test_concepto_con_nombre_normalizado(d):
    ibi = next(c for c in cap(d, 1)["conceptos"] if c["codigo"] == "113")
    assert ibi["nombre"] == "Impuesto sobre bienes inmuebles de naturaleza urbana"
    assert ibi["y2026"] == 11675000


def test_los_conceptos_suman_el_total_del_capitulo(d):
    for c in d["capitulos"]:
        suma = sum(x["y2026"] or 0 for x in c["conceptos"])
        assert suma == pytest.approx(c["y2026"], abs=1), f"capítulo {c['cap']}"


def test_sin_articulos_ni_totales_como_conceptos(d):
    for c in d["capitulos"]:
        for x in c["conceptos"]:
            assert not x["nombre"].upper().startswith(("ARTÍCULO", "TOTAL"))
