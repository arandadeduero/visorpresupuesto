import json

import pytest

from budget.resumen import parse_resumen

ANIOS = [2024, 2025, 2026]

# Valores leídos a mano de la hoja «<año>» de cada A1 (previsiones del año y créditos del año anterior).
ESPERADO = {
    2024: {
        "totalGastos": 49800478.98, "totalIngresos": 49800478.98, "totalGastosAnterior": 46698377.61,
        "g1": (14908290.5, 13537729.0), "g6": (12435470.48, 13784278.61), "i1": 14678000, "i9": 8618380.98,
        "por100": [25, 39, 30, 6], "obras": 12565470.48, "habitantes": 33757, "anioPoblacion": 2024,
    },
    2025: {
        "totalGastos": 64828315.2, "totalIngresos": 65078315.2, "totalGastosAnterior": 49800478.98,
        "g1": (15562398.5, 14908290.5), "g6": (27237906.7, 12435470.48), "i1": 15820000, "i9": 20457492.93,
        "por100": [42, 30, 24, 4], "obras": 27337906.7, "habitantes": 33956, "anioPoblacion": 2025,
    },
    2026: {
        "totalGastos": 64280861.35, "totalIngresos": 64280861.35, "totalGastosAnterior": 65078315.2,
        "g1": (15616598.5, 15562398.5), "g6": (24206942.85, 27237906.7), "i1": 16600000, "i9": 20161623.64,
        "por100": [38, 34, 24, 4], "obras": 24326942.85, "habitantes": 33956, "anioPoblacion": 2025,
    },
}


@pytest.fixture(scope="module", params=ANIOS)
def caso(request):
    return request.param, parse_resumen(request.param), ESPERADO[request.param]


def cap(lista, n):
    return next(c for c in lista if c["cap"] == n)


def test_totales(caso):
    anio, r, e = caso
    assert r["totalGastos"] == pytest.approx(e["totalGastos"], abs=0.01)
    assert r["totalIngresos"] == pytest.approx(e["totalIngresos"], abs=0.01)
    assert r["totalGastosAnterior"] == pytest.approx(e["totalGastosAnterior"], abs=0.01)
    assert r["anio"] == anio and r["tipo"] == "inicial"


def test_capitulos_de_gastos_e_ingresos(caso):
    _, r, e = caso
    assert len(r["gastosPorCapitulo"]) == 9 and len(r["ingresosPorCapitulo"]) == 9
    g1 = cap(r["gastosPorCapitulo"], 1)
    assert (g1["actual"], g1["anterior"]) == e["g1"]
    assert g1["corto"] == "Personal" and g1["oficial"] == "Gastos de personal"
    g6 = cap(r["gastosPorCapitulo"], 6)
    assert (g6["actual"], g6["anterior"]) == e["g6"]
    assert cap(r["ingresosPorCapitulo"], 1)["actual"] == e["i1"]
    assert cap(r["ingresosPorCapitulo"], 9)["actual"] == e["i9"]


def test_los_capitulos_suman_el_total(caso):
    _, r, _ = caso
    assert sum(c["actual"] for c in r["gastosPorCapitulo"]) == pytest.approx(r["totalGastos"], abs=0.01)
    assert sum(c["actual"] for c in r["ingresosPorCapitulo"]) == pytest.approx(r["totalIngresos"], abs=0.01)
    assert sum(c["anterior"] for c in r["gastosPorCapitulo"]) == pytest.approx(r["totalGastosAnterior"], abs=0.01)


def test_por_cada_100_euros(caso):
    _, r, e = caso
    assert [b["bloque"] for b in r["por100"]] == ["Obras e inversiones", "Servicios", "Personal", "Otros"]
    assert [b["euros"] for b in r["por100"]] == e["por100"]
    assert r["por100"][0]["importe"] == pytest.approx(e["obras"], abs=0.01)
    assert sum(b["importe"] for b in r["por100"]) == pytest.approx(r["totalGastos"], abs=0.01)


def test_json_limpio(caso):
    texto = json.dumps(caso[1], ensure_ascii=False)
    assert "#REF" not in texto and "NaN" not in texto


def test_habitantes_para_los_importes_por_vecino(caso):
    _, r, e = caso
    assert r["habitantes"] == e["habitantes"]
    assert r["anioPoblacion"] == e["anioPoblacion"]
    assert "INE" in r["fuentePoblacion"]


def test_sin_notas_en_el_parser_las_pone_el_conversor(caso):
    assert "notas" not in caso[1]
