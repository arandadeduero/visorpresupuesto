import pytest

from budget.inversiones import parse_inversiones

ANIOS = [2024, 2025, 2026]

# Fila «TOTAL CAPÍTULO VI» de cada A9: importe, préstamo, ingresos corrientes, otros, remanente (RTA) y subvenciones.
ESPERADO = {
    2024: {
        "total": 12435470.48,
        "fuentes": {"prestamo": 8618380.98, "ingresosCorrientes": 188138.44, "otros": 80240.4, "rta": 2157195.5, "subvenciones": 1391515.16},
    },
    2025: {
        "total": 27237906.7,
        "fuentes": {"prestamo": 20457492.93, "ingresosCorrientes": 366893.61, "otros": 0, "rta": 4556700.16, "subvenciones": 1856820},
    },
    2026: {
        "total": 24206942.85,
        "fuentes": {"prestamo": 20161623.64, "ingresosCorrientes": 2416188.11, "otros": 0, "rta": 183530.15, "subvenciones": 1445600.95},
    },
}


@pytest.fixture(scope="module", params=ANIOS)
def caso(request):
    return request.param, parse_inversiones(request.param), ESPERADO[request.param]


def programa(d, codigo):
    return next(p for p in d["programas"] if p["codigo"] == codigo)


def proyectos(d, codigo):
    return {p["nombre"]: p for p in programa(d, codigo)["proyectos"]}


def test_total_y_fuentes_de_financiacion(caso):
    _, d, e = caso
    assert d["total"] == pytest.approx(e["total"], abs=0.01)
    assert d["fuentes"] == pytest.approx(e["fuentes"], abs=0.01)
    assert sum(d["fuentes"].values()) == pytest.approx(d["total"], abs=0.01)


def test_coherencia_y_sin_notas_de_trabajo(caso):
    _, d, _ = caso
    assert len({p["codigo"] for p in d["programas"]}) == len(d["programas"]), "programa repetido"
    assert sum(p["total"] for p in d["programas"]) == pytest.approx(d["total"], abs=1)
    for p in d["programas"]:
        assert p["total"] == pytest.approx(sum(pr["importe"] for pr in p["proyectos"]), abs=0.01)
        for pr in p["proyectos"]:
            assert "!!!" not in pr["nombre"] and "??" not in pr["nombre"]
            assert pr["importe"] == pytest.approx(sum(pr[f] for f in ("prestamo", "ingresosCorrientes", "otros", "rta", "subvenciones")), abs=0.01), pr["nombre"]


def test_programa_seguridad_2026_con_sus_proyectos():
    d = parse_inversiones(2026)
    seg = programa(d, "1320")
    assert seg["nombre"] == "Seguridad" and seg["total"] == 155000
    p = proyectos(d, "1320")
    camaras = p["Cámaras de seguridad y tráfico"]
    assert camaras["importe"] == 60000 and camaras["prestamo"] == 60000 and camaras["partida"] == "622"
    assert p["Redacción planta baja edificio"]["importe"] == 50000
    furgoneta = p["Adquisición furgoneta"]
    assert furgoneta["importe"] == 45000 and furgoneta["partida"] == "624"


def test_fuente_distinta_del_prestamo_2026():
    sem = proyectos(parse_inversiones(2026), "1330")["Mejora de semáforos y señalética"]
    assert sem["ingresosCorrientes"] == 30000 and sem["prestamo"] == 0


def test_2024_la_tabla_empieza_una_columna_antes_y_se_lee_igual():
    d = parse_inversiones(2024)
    seg = programa(d, "1320")
    assert seg["nombre"] == "Seguridad" and seg["total"] == 67000
    p = proyectos(d, "1320")
    assert p["Sistema portátil velocidad"]["importe"] == 16000 and p["Sistema portátil velocidad"]["partida"] == "623"
    assert p["Software policía"]["importe"] == 33000 and p["Software policía"]["partida"] == "641"
    # proyecto con varias fuentes: 815.333,40 € = 187.772,57 préstamo + 74.240,40 otros + 553.320,43 subvenciones
    santa = proyectos(d, "1522")["Rehabilitación viviendas Junta Santa Catalina"]
    assert (santa["importe"], santa["prestamo"], santa["otros"], santa["subvenciones"]) == (815333.4, 187772.57, 74240.4, 553320.43)
    assert santa["partida"] == "650"


def test_2025_el_bloque_duplicado_de_participacion_ciudadana_solo_cuenta_una_vez():
    # El Excel de 2025 deja dos bloques «9240»; el primero (5.000 €) es una copia vieja y no suma en el total del capítulo.
    d = parse_inversiones(2025)
    assert programa(d, "9240")["total"] == 345000
    p = proyectos(d, "9240")
    assert p["Ventanas Teleclub Sinovas"]["importe"] == 5000
    assert p["Adquisición y rehabilitación de bajo en Santa Catalina"]["importe"] == 340000
    assert "Termostatos asuntos económicos" not in p
    assert proyectos(d, "1320")["Redacción planta baja edificio para sala de tiro"]["partida"] == "622"
    assert proyectos(d, "1330")["Mejora de semáforos"]["importe"] == 25000
