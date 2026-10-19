from datetime import date

import pytest

from budget.deuda import parse_deuda, project_balance

ANIOS = [2024, 2025, 2026]

# Saldos «DEUDA VIVA 01/01» y «31/12» del año de cada préstamo, leídos a mano de cada A13.1.
VIVA = {
    2024: {"BANKIA": (135948.27, 99695.43), "UNICAJA BANCO": (1025812.27, 820649.83), "CAJA LABORAL": (2615739.17, 2325101.48)},
    2025: {"BANKIA": (99695.43, 63442.59), "UNICAJA BANCO": (820649.83, 615487.39), "CAJA LABORAL": (2325101.48, 2034463.79)},
    2026: {"BANKIA": (63442.59, 27189.75), "UNICAJA BANCO": (615487.39, 410324.95), "CAJA LABORAL": (2034463.79, 1743826.11)},
}
# Totales de la hoja «Hoja1» de A13.2 (intereses y amortización) y total de intereses con el préstamo previsto.
CARGA = {
    2024: {"intereses": 147840.30, "amortizacion": 532052.98, "con_previsto": None},
    2025: {"intereses": 101122.07, "amortizacion": 532052.98, "con_previsto": 489445.83},
    2026: {"intereses": 65378.59, "amortizacion": 532052.98, "con_previsto": 355709.37},
}
# Deuda a 31/12 de cada año del anexo (suma de los tres préstamos).
CIERRES = {2022: 4309552.67, 2023: 3777499.71, 2024: 3245446.74, 2025: 2713393.77, 2026: 2181340.81}


@pytest.fixture(scope="module", params=ANIOS)
def caso(request):
    return request.param, parse_deuda(request.param)


def test_tres_prestamos_existentes(caso):
    anio, d = caso
    por_entidad = {p["entidad"]: p for p in d["prestamos"]}
    assert set(por_entidad) == {"BANKIA", "UNICAJA BANCO", "CAJA LABORAL"}
    assert por_entidad["BANKIA"]["fecha"] == "2017-11-27"
    assert por_entidad["BANKIA"]["importe"] == 362528.65
    assert por_entidad["BANKIA"]["ultimaAmortizacion"] == "2027-09-30"
    assert por_entidad["BANKIA"]["tipoInteres"].startswith("EURIBOR")
    for ent, (ini, fin) in VIVA[anio].items():
        assert por_entidad[ent]["vivaInicio"] == pytest.approx(ini, abs=0.01)
        assert por_entidad[ent]["vivaFin"] == pytest.approx(fin, abs=0.01)
        assert por_entidad[ent]["vivaInicio"] - por_entidad[ent]["amortizacion"] == pytest.approx(por_entidad[ent]["vivaFin"], abs=0.02)


def test_serie_solo_con_prestamos_existentes(caso):
    anio, d = caso
    serie = {s["anio"]: s["viva"] for s in d["serie"]}
    # Desde 2022 (saldo a 1 de enero de 2023) hasta el último año con deuda; los años cerrados salen del Excel y los siguientes se proyectan.
    for a, viva in CIERRES.items():
        assert serie[a] == pytest.approx(viva, abs=0.02), a
    assert serie[2027] == pytest.approx(1658350.94, abs=1)
    assert serie[2028] == pytest.approx(1162550.75, abs=1)
    assert d["serie"][-1] == {"anio": 2032, "viva": 0}
    assert [s["anio"] for s in d["serie"]] == list(range(2022, 2033))


def test_titular_y_carga_financiera(caso):
    anio, d = caso
    assert d["titular"]["vivaFin"] == pytest.approx(CIERRES[anio], abs=0.02)
    c = CARGA[anio]
    assert d["carga"]["intereses"] == pytest.approx(c["intereses"], abs=0.01)
    assert d["carga"]["amortizacion"] == pytest.approx(c["amortizacion"], abs=0.01)
    assert d["carga"]["total"] == pytest.approx(c["intereses"] + c["amortizacion"], abs=0.02)
    if c["con_previsto"] is None:
        assert d["carga"]["interesesConPrevisto"] is None
    else:
        assert d["carga"]["interesesConPrevisto"] == pytest.approx(c["con_previsto"], abs=0.01)


def test_la_amortizacion_de_la_carga_son_las_cuotas_de_los_prestamos(caso):
    _, d = caso
    assert sum(p["amortizacion"] for p in d["prestamos"]) == pytest.approx(d["carga"]["amortizacion"], abs=1)


def test_prestamo_previsto_aparte_2026():
    d = parse_deuda(2026)
    pv = d["previsto"]
    assert pv["importe"] == 11000000
    assert pv["fecha"] == "2026-03-01"
    assert pv["primeraAmortizacion"] == "2027-12-31" and pv["ultimaAmortizacion"] == "2037-12-31"
    assert d["titular"]["vivaFinConPrevisto"] == pytest.approx(13181340.81, abs=0.01)


def test_prestamo_previsto_2025_se_firmaria_en_marzo_de_2025():
    d = parse_deuda(2025)
    pv = d["previsto"]
    assert pv["importe"] == 11000000 and pv["fecha"] == "2025-03-01"
    assert pv["primeraAmortizacion"] == "2026-12-31" and pv["ultimaAmortizacion"] == "2036-12-31"
    assert d["titular"]["vivaFinConPrevisto"] == pytest.approx(13713393.78, abs=0.02)  # total del anexo: 13.713.393,78 €


def test_2024_no_tiene_prestamo_previsto():
    d = parse_deuda(2024)
    assert d["previsto"] is None
    assert d["titular"]["vivaFinConPrevisto"] is None
    assert d["carga"]["interesesConPrevisto"] is None


def test_project_balance_cuota_constante():
    # Caja Laboral: 1.743.826,11 vivos a fin de 2026, 290.637,68 al año, última amortización 2032-12-31
    assert project_balance(1743826.11, 290637.68, 2026, date(2032, 12, 31), 2027) == pytest.approx(1453188.43, abs=0.01)
    assert project_balance(1743826.11, 290637.68, 2026, date(2032, 12, 31), 2032) == 0
    assert project_balance(27189.75, 36252.84, 2026, date(2027, 9, 30), 2027) == 0
