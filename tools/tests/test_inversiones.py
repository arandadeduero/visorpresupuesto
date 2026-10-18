import pytest

from budget.inversiones import parse_inversiones


@pytest.fixture(scope="module")
def d():
    return parse_inversiones(2026)


def programa(d, codigo):
    return next(p for p in d["programas"] if p["codigo"] == codigo)


def test_total_y_fuentes_de_financiacion(d):
    assert d["total"] == pytest.approx(24206942.85, abs=0.01)
    esperado = {
        "prestamo": 20161623.64,
        "ingresosCorrientes": 2416188.11,
        "otros": 0,
        "rta": 183530.15,
        "subvenciones": 1445600.95,
    }
    assert d["fuentes"] == pytest.approx(esperado, abs=0.01)


def test_programa_seguridad_con_sus_proyectos(d):
    seg = programa(d, "1320")
    assert seg["nombre"] == "Seguridad" and seg["total"] == 155000
    proyectos = {p["nombre"]: p for p in seg["proyectos"]}
    camaras = proyectos["Cámaras de seguridad y tráfico"]
    assert camaras["importe"] == 60000 and camaras["prestamo"] == 60000 and camaras["partida"] == "622"
    assert proyectos["Redacción planta baja edificio"]["importe"] == 50000
    furgoneta = proyectos["Adquisición furgoneta"]
    assert furgoneta["importe"] == 45000 and furgoneta["partida"] == "624"


def test_fuente_distinta_del_prestamo(d):
    sem = next(p for p in programa(d, "1330")["proyectos"] if p["nombre"] == "Mejora de semáforos y señalética")
    assert sem["ingresosCorrientes"] == 30000 and sem["prestamo"] == 0


def test_coherencia_y_sin_notas_de_trabajo(d):
    assert sum(p["total"] for p in d["programas"]) == pytest.approx(d["total"], abs=1)
    for p in d["programas"]:
        for pr in p["proyectos"]:
            assert "!!!" not in pr["nombre"] and "??" not in pr["nombre"]
