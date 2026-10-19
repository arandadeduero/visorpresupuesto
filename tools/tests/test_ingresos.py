import pytest

from budget.ingresos import parse_ingresos

ANIOS = [2024, 2025, 2026]

# Capítulo 1 y capítulo 9 (anterior2, anterior, actual) y el IBI urbano (113), leídos a mano de cada A2.
# En 2024 y 2025 el Excel solo trae dos años (no hay «anterior2»); en 2024 la columna del año anterior se llama «PREVISIONES».
ESPERADO = {
    2024: {"c1": (None, 14650000, 14678000), "c9": 8618380.98, "ibi": (None, 10653000, 10550000)},
    2025: {"c1": (None, 14678000, 15820000), "c9": 20457492.93, "ibi": (None, 10550000, 11400000)},
    2026: {"c1": (14678000, 15820000, 16600000), "c9": 20161623.64, "ibi": (10550000, 11400000, 11675000)},
}


@pytest.fixture(scope="module", params=ANIOS)
def caso(request):
    return request.param, parse_ingresos(request.param), ESPERADO[request.param]


def cap(d, n):
    return next(c for c in d["capitulos"] if c["cap"] == n)


def test_nueve_capitulos_con_totales(caso):
    anio, d, e = caso
    assert d["anio"] == anio
    assert [c["cap"] for c in d["capitulos"]] == list(range(1, 10))
    c1 = cap(d, 1)
    assert (c1["anterior2"], c1["anterior"], c1["actual"]) == e["c1"]
    assert cap(d, 9)["actual"] == e["c9"]
    assert c1["corto"].startswith("Impuestos directos")


def test_concepto_con_nombre_normalizado(caso):
    _, d, e = caso
    ibi = next(c for c in cap(d, 1)["conceptos"] if c["codigo"] == "113")
    assert ibi["nombre"] == "Impuesto sobre bienes inmuebles de naturaleza urbana"
    assert (ibi["anterior2"], ibi["anterior"], ibi["actual"]) == e["ibi"]


def test_los_conceptos_suman_el_total_del_capitulo(caso):
    _, d, _ = caso
    for c in d["capitulos"]:
        suma = sum(x["actual"] or 0 for x in c["conceptos"])
        assert suma == pytest.approx(c["actual"], abs=1), f"capítulo {c['cap']}"


def test_sin_articulos_ni_totales_como_conceptos(caso):
    for c in caso[1]["capitulos"]:
        for x in c["conceptos"]:
            assert not x["nombre"].upper().startswith(("ARTÍCULO", "TOTAL"))


def test_2024_el_total_roto_del_capitulo_8_se_recompone_con_sus_conceptos():
    # En el Excel de 2024 el total de 2023 del capítulo VIII es «#REF!»: se suman sus conceptos (830.00: 15.000 € y 870.10: 0 €).
    c8 = cap(parse_ingresos(2024), 8)
    assert c8["anterior"] == 15000 and c8["actual"] == 2172195.5


def test_solo_2026_trae_tres_anios():
    for anio in (2024, 2025):
        assert all(x["anterior2"] is None for c in parse_ingresos(anio)["capitulos"] for x in c["conceptos"])
    assert any(x["anterior2"] for c in parse_ingresos(2026)["capitulos"] for x in c["conceptos"])


# Artículos (dos primeros dígitos del concepto): 11 «Impuestos sobre el capital», 29 «Otros impuestos indirectos»,
# 91 «Préstamos recibidos en euros». Importes del año del presupuesto, leídos de las filas «ARTÍCULO nn» de cada A2.
ARTICULOS = {
    2024: {"11": 13228000, "29": 900000, "91": 8618380.98},
    2025: {"11": 14320000, "29": 900000, "91": 20457492.93},
    2026: {"11": 14850000, "29": 900000, "91": 20161623.64},
}


def articulo(d, codigo):
    return next(a for c in d["capitulos"] for a in c["articulos"] if a["codigo"] == codigo)


def test_los_articulos_cuadran_con_el_excel(caso):
    anio, d, _ = caso
    for codigo, importe in ARTICULOS[anio].items():
        assert articulo(d, codigo)["actual"] == pytest.approx(importe, abs=0.01)


def test_prestamos_es_el_articulo_91_con_nombre_oficial():
    a = articulo(parse_ingresos(2026), "91")
    assert a["actual"] == 20161623.64 and a["anterior"] == 20457492.93 and a["anterior2"] == 8618380.98
    assert a["nombre"] == "Préstamos recibidos" and a["oficial"] == "Préstamos recibidos en euros"


def test_los_articulos_suman_el_capitulo_y_todos_tienen_nombre(caso):
    _, d, _ = caso
    for c in d["capitulos"]:
        assert c["articulos"], f"capítulo {c['cap']} sin artículos"
        for campo in ("anterior", "actual"):
            if c[campo] is not None:
                assert sum(a[campo] or 0 for a in c["articulos"]) == pytest.approx(c[campo], abs=1)
        for a in c["articulos"]:
            assert a["codigo"].startswith(str(c["cap"]))
            assert not a["nombre"].startswith("Artículo "), f"artículo {a['codigo']} sin nombre oficial"
        assert [a["codigo"] for a in c["articulos"]] == sorted(a["codigo"] for a in c["articulos"])
        for x in c["conceptos"]:
            assert x["articulo"] == x["codigo"][:2]


def test_las_tasas_por_dominio_publico_son_el_articulo_33():
    a = articulo(parse_ingresos(2026), "33")
    assert a["oficial"].startswith("Tasas por la utilización privativa")
