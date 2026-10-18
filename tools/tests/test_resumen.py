import json

import pytest

from budget.resumen import parse_resumen


@pytest.fixture(scope="module")
def r():
    return parse_resumen(2026)


def cap(lista, n):
    return next(c for c in lista if c["cap"] == n)


def test_totales(r):
    assert r["totalGastos"] == pytest.approx(64280861.35, abs=0.01)
    assert r["totalIngresos"] == pytest.approx(64280861.35, abs=0.01)
    assert r["totalGastos2025"] == pytest.approx(65078315.2, abs=0.01)
    assert r["anio"] == 2026 and r["tipo"] == "inicial"


def test_capitulos_de_gastos_e_ingresos(r):
    assert len(r["gastosPorCapitulo"]) == 9 and len(r["ingresosPorCapitulo"]) == 9
    g1 = cap(r["gastosPorCapitulo"], 1)
    assert g1["y2026"] == 15616598.5 and g1["y2025"] == 15562398.5
    assert g1["corto"] == "Personal" and g1["oficial"] == "Gastos de personal"
    assert cap(r["gastosPorCapitulo"], 6)["y2026"] == 24206942.85
    assert cap(r["ingresosPorCapitulo"], 1)["y2026"] == 16600000
    assert cap(r["ingresosPorCapitulo"], 9)["y2026"] == 20161623.64


def test_por_cada_100_euros(r):
    assert [b["bloque"] for b in r["por100"]] == ["Obras e inversiones", "Servicios", "Personal", "Otros"]
    assert [b["euros"] for b in r["por100"]] == [38, 34, 24, 4]
    assert r["por100"][0]["importe"] == pytest.approx(24326942.85, abs=0.01)
    assert sum(b["importe"] for b in r["por100"]) == pytest.approx(r["totalGastos"], abs=0.01)


def test_json_limpio(r):
    texto = json.dumps(r, ensure_ascii=False)
    assert "#REF" not in texto and "NaN" not in texto


def test_habitantes_para_los_importes_por_vecino(r):
    assert r["habitantes"] == 33956
    assert r["anioPoblacion"] == 2025
    assert "INE" in r["fuentePoblacion"]
