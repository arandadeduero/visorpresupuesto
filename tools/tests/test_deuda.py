from datetime import date

import pytest

from budget.deuda import parse_deuda, project_balance


@pytest.fixture(scope="module")
def d():
    return parse_deuda(2026)


def test_tres_prestamos_existentes(d):
    por_entidad = {p["entidad"]: p for p in d["prestamos"]}
    assert set(por_entidad) == {"BANKIA", "UNICAJA BANCO", "CAJA LABORAL"}
    assert por_entidad["BANKIA"]["fecha"] == "2017-11-27"
    assert por_entidad["BANKIA"]["importe"] == 362528.65
    assert por_entidad["BANKIA"]["ultimaAmortizacion"] == "2027-09-30"
    assert por_entidad["BANKIA"]["tipoInteres"].startswith("EURIBOR")
    esperado = {"BANKIA": (63442.59, 27189.75), "UNICAJA BANCO": (615487.39, 410324.95), "CAJA LABORAL": (2034463.79, 1743826.11)}
    for ent, (ini, fin) in esperado.items():
        assert por_entidad[ent]["vivaInicio"] == pytest.approx(ini, abs=0.01)
        assert por_entidad[ent]["vivaFin"] == pytest.approx(fin, abs=0.01)


def test_prestamo_previsto_aparte(d):
    pv = d["previsto"]
    assert pv["importe"] == 11000000
    assert pv["fecha"] == "2026-03-01"
    assert pv["primeraAmortizacion"] == "2027-12-31" and pv["ultimaAmortizacion"] == "2037-12-31"


def test_serie_solo_con_prestamos_existentes(d):
    serie = {s["anio"]: s["viva"] for s in d["serie"]}
    assert serie[2022] == pytest.approx(4309552.67, abs=0.01)
    assert serie[2023] == pytest.approx(3777499.71, abs=0.01)
    assert serie[2024] == pytest.approx(3245446.74, abs=0.01)
    assert serie[2025] == pytest.approx(2713393.77, abs=0.01)
    assert serie[2026] == pytest.approx(2181340.81, abs=0.01)
    assert serie[2027] == pytest.approx(1658350.94, abs=1)
    assert serie[2028] == pytest.approx(1162550.75, abs=1)
    assert d["serie"][-1] == {"anio": 2032, "viva": 0}


def test_titular_y_carga_financiera(d):
    assert d["titular"]["vivaFin"] == pytest.approx(2181340.81, abs=0.01)
    assert d["titular"]["vivaFinConPrevisto"] == pytest.approx(13181340.81, abs=0.01)
    assert d["carga"]["intereses"] == pytest.approx(65378.59, abs=0.01)
    assert d["carga"]["amortizacion"] == pytest.approx(532052.98, abs=0.01)
    assert d["carga"]["total"] == pytest.approx(65378.59 + 532052.98, abs=0.02)
    assert d["carga"]["interesesConPrevisto"] == pytest.approx(355709.37, abs=0.01)


def test_project_balance_cuota_constante():
    # Caja Laboral: 1.743.826,11 vivos a fin de 2026, 290.637,68 al año, última amortización 2032-12-31
    assert project_balance(1743826.11, 290637.68, 2026, date(2032, 12, 31), 2027) == pytest.approx(1453188.43, abs=0.01)
    assert project_balance(1743826.11, 290637.68, 2026, date(2032, 12, 31), 2032) == 0
    assert project_balance(27189.75, 36252.84, 2026, date(2027, 9, 30), 2027) == 0
