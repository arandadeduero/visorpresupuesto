import pytest

from budget.subvenciones import parse_subvenciones


@pytest.fixture(scope="module")
def d():
    return parse_subvenciones(2026)


def programa(d, partida):
    return next(p for p in d["programas"] if p["partida"] == partida)


def item(p, entidad):
    return next(i for i in p["items"] if i["entidad"] == entidad)


def test_cruz_roja_en_asistencia_social(d):
    p = programa(d, "2311 489.00")
    assert p["programa"] == "Asistencia social primaria"
    cruz = item(p, "Cruz Roja")
    assert (cruz["anterior"], cruz["actual"]) == (10000, 10000)
    assert cruz["objeto"] == "Actividades sociales"
    assert item(p, "Cáritas")["actual"] == 3000


def test_entidad_en_programa_pequeno(d):
    assert item(programa(d, "1700 489.00"), "Club Deportivo Espeleoduero")["actual"] == 2000


def test_totales_coherentes(d):
    assert d["total"] > 0
    assert d["total"] == pytest.approx(sum(p["actual"] for p in d["programas"]), abs=0.01)
    assert d["total"] == pytest.approx(sum(e["actual"] for e in d["entidades"]), abs=0.01)
    assert d["totalAnterior"] == pytest.approx(sum(e["anterior"] for e in d["entidades"]), abs=0.01)


def test_entidades_agrupadas_sin_tildes_ni_mayusculas(d):
    nombres = [e["entidad"] for e in d["entidades"]]
    assert all(n.strip() for n in nombres)
    claves = [n.lower() for n in nombres]
    assert len(claves) == len(set(claves))
    cruz = next(e for e in d["entidades"] if e["entidad"] == "Cruz Roja")
    assert "Asistencia social primaria" in cruz["programas"]
