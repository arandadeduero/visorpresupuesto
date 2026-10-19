import pytest

from budget.gastos import parse_gastos

ANIOS = [2024, 2025, 2026]

# Totales «TOTAL CAPÍTULO …» de cada A3 y algunos programas, leídos a mano de las hojas «<año>».
ESPERADO = {
    2024: {
        "caps": {1: 14908290.5, 2: 19550670, 3: 170300, 4: 1955748, 5: 100000, 6: 12435470.48, 7: 130000, 8: 15000, 9: 535000},
        "total": 49800478.98, "p1300": 176700, "p1320": 2525600, "p1320_total": 2525600 + 173100 + 67000,
        "inv1320": {"623": 34000, "641": 33000}, "sin_anterior": [6],
    },
    2025: {
        "caps": {1: 15562398.5, 2: 19430030, 3: 170300, 4: 1727680, 5: 50000, 6: 27237906.7, 7: 100000, 8: 15000, 9: 535000},
        "total": 64828315.2, "p1300": 177175, "p1320": 2494600, "p1320_total": 2494600 + 246100 + 20000,
        "inv1320": {"622": 20000}, "sin_anterior": [6],
    },
    2026: {
        "caps": {1: 15616598.5, 2: 21623640, 3: 184000, 4: 1929680, 5: 50000, 6: 24206942.85, 7: 120000, 8: 15000, 9: 535000},
        "total": 64280861.35, "p1300": 177175, "p1320": 2494600, "p1320_total": 2494600 + 244100 + 155000,
        "inv1320": {"622": 110000, "624": 45000}, "sin_anterior": [],
    },
}


@pytest.fixture(scope="module", params=ANIOS)
def caso(request):
    return request.param, parse_gastos(request.param), ESPERADO[request.param]


def test_totales_por_capitulo(caso):
    _, d, e = caso
    assert {c["cap"]: c["actual"] for c in d["capitulos"]} == pytest.approx(e["caps"], abs=0.01)


def test_las_partidas_suman_el_total_de_cada_capitulo(caso):
    _, d, _ = caso
    for c in d["capitulos"]:
        suma = sum(p["actual"] or 0 for p in d["partidas"] if p["cap"] == c["cap"])
        assert suma == pytest.approx(c["actual"], abs=1), f"capítulo {c['cap']}"


def test_personal_solo_agrupado_por_programa(caso):
    _, d, e = caso
    personal = [p for p in d["partidas"] if p["cap"] == 1]
    assert all(p["codigo"] is None and p["nombre"] == "Gastos de personal" for p in personal)
    por_programa = {p["programa"]: p["actual"] for p in personal}
    assert por_programa["1300"] == e["p1300"]
    assert por_programa["1320"] == e["p1320"]
    assert len(personal) == len(por_programa)


def test_inversiones_llegan_a_la_partida(caso):
    _, d, e = caso
    seg = {p["codigo"]: p["actual"] for p in d["partidas"] if p["cap"] == 6 and p["programa"] == "1320"}
    # En 2024 la partida 623 (34.000 €) y la 641 (33.000 €) suman los 67.000 € del programa 1320.
    assert seg == e["inv1320"]


def test_programas_con_nombre_y_area(caso):
    _, d, e = caso
    assert all(p["nombre"] for p in d["programas"])
    assert {p["area"] for p in d["programas"]} <= {0, 1, 2, 3, 4, 9}
    assert {a["area"] for a in d["areas"]} == {p["area"] for p in d["programas"]}
    seg = next(p for p in d["programas"] if p["codigo"] == "1320")
    assert seg["area"] == 1 and seg["nombre"] == "Seguridad"
    assert seg["actual"] == e["p1320_total"]
    assert next(p for p in d["programas"] if p["codigo"] == "0110")["area"] == 0


def test_los_programas_suman_el_total(caso):
    _, d, e = caso
    assert sum(p["actual"] for p in d["programas"]) == pytest.approx(e["total"], abs=1)


def test_politicas_de_gasto_con_nombre_llano(caso):
    _, d, e = caso
    politicas = {p["codigo"]: p for p in d["politicas"]}
    assert politicas["13"]["nombre"] == "Seguridad y movilidad ciudadana"
    assert politicas["01"]["nombre"] == "Deuda pública" and politicas["01"]["area"] == 0
    assert politicas["34"]["nombre"] == "Deporte" and politicas["33"]["nombre"] == "Cultura"
    assert politicas["92"]["area"] == 9
    assert not any(p["nombre"].startswith("Política ") for p in politicas.values()), "política sin nombre en labels.py"
    assert sum(p["actual"] for p in politicas.values()) == pytest.approx(e["total"], abs=1)


def test_cada_programa_cuelga_de_una_politica_conocida(caso):
    _, d, _ = caso
    codigos = {p["codigo"] for p in d["politicas"]}
    for p in d["programas"]:
        assert p["politica"] == p["codigo"][:2]
        assert p["politica"] in codigos
    seg = next(p for p in d["politicas"] if p["codigo"] == "13")
    assert seg["actual"] == pytest.approx(sum(p["actual"] for p in d["programas"] if p["politica"] == "13"), abs=0.01)


def test_los_capitulos_usan_los_creditos_del_anio_anterior_de_a1(caso):
    # La columna del año anterior de A3 no es fiable (no trae las inversiones): los capítulos usan la cifra de A1.
    from budget.resumen import parse_resumen

    anio, d, _ = caso
    a1 = {c["cap"]: c["anterior"] for c in parse_resumen(anio)["gastosPorCapitulo"]}
    assert {c["cap"]: c["anterior"] for c in d["capitulos"]} == a1


def test_las_inversiones_del_anio_anterior_que_a3_no_trae_quedan_sin_dato_y_no_como_cero(caso):
    _, d, e = caso
    assert d["sinAnterior"] == e["sin_anterior"]
    for p in d["partidas"]:
        assert (p["anterior"] is None) == (p["cap"] in e["sin_anterior"]), p
    # un programa o una política con alguna partida sin año anterior no tiene variación calculable
    con_inversion = {p["programa"] for p in d["partidas"] if p["cap"] in e["sin_anterior"]}
    for prog in d["programas"]:
        assert (prog["anterior"] is None) == (prog["codigo"] in con_inversion)
    for pol in d["politicas"]:
        hijos = [p for p in d["programas"] if p["politica"] == pol["codigo"]]
        assert (pol["anterior"] is None) == any(h["anterior"] is None for h in hijos)


def test_sin_errores_de_excel(caso):
    assert "#REF" not in str(caso[1])


def articulo(d, cap, codigo):
    return next(a for a in d["articulos"] if a["cap"] == cap and a["codigo"] == codigo)


def test_los_articulos_suman_el_total_de_cada_capitulo(caso):
    _, d, _ = caso
    for c in d["capitulos"]:
        delcap = [a for a in d["articulos"] if a["cap"] == c["cap"]]
        assert delcap, f"capítulo {c['cap']} sin artículos"
        assert sum(a["actual"] for a in delcap) == pytest.approx(c["actual"], abs=1)
        for a in delcap:
            assert a["codigo"].startswith(str(c["cap"]))
            assert not a["nombre"].startswith("Artículo "), f"artículo {a['codigo']} sin nombre"
            if c["cap"] in d["sinAnterior"]:
                assert a["anterior"] is None


def test_cada_partida_tiene_su_articulo_salvo_el_personal(caso):
    _, d, _ = caso
    for p in d["partidas"]:
        if p["cap"] == 1:
            assert p["articulo"] is None
        else:
            assert p["articulo"] == p["codigo"][:2]
            assert any(a["codigo"] == p["articulo"] for a in d["articulos"])


def test_el_personal_tambien_tiene_articulos(caso):
    _, d, _ = caso
    codigos = {a["codigo"] for a in d["articulos"] if a["cap"] == 1}
    assert {"12", "13", "16"} <= codigos
    assert articulo(d, 1, "12")["nombre"] == "Personal funcionario"


def test_amortizacion_de_prestamos_es_el_articulo_91(caso):
    _, d, _ = caso
    a = articulo(d, 9, "91")
    assert a["actual"] == 535000 and a["oficial"] == "Amortización de préstamos y de operaciones en euros"


def test_2026_el_articulo_27_no_existe_en_la_clasificacion_oficial_y_lleva_nombre_neutro():
    a = articulo(parse_gastos(2026), 2, "27")
    assert "suprimido" in a["oficial"] and a["nombre"] == "Otros gastos en bienes y servicios"
