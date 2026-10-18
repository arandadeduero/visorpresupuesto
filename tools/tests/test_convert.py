import copy
import json

import pytest

import convert as conv

NOMBRES = ["resumen", "ingresos", "gastos", "inversiones", "subvenciones", "deuda"]


@pytest.fixture(scope="module")
def generado(tmp_path_factory):
    out = tmp_path_factory.mktemp("data")
    avisos = conv.convert(2026, out)
    return out, avisos


def test_escribe_los_seis_json_y_el_indice(generado):
    out, _ = generado
    for n in NOMBRES:
        datos = json.loads((out / "2026" / f"{n}.json").read_text(encoding="utf-8"))
        assert datos["anio"] == 2026
    assert json.loads((out / "index.json").read_text(encoding="utf-8")) == {
        "anios": [{"anio": 2026, "tipo": "inicial"}],
        "ultimo": 2026,
    }


def test_los_datos_de_2026_cuadran(generado):
    assert generado[1] == []


def test_convertir_dos_veces_no_duplica_el_anio(generado):
    out, _ = generado
    conv.convert(2026, out)
    assert len(json.loads((out / "index.json").read_text(encoding="utf-8"))["anios"]) == 1


def test_check_totals_avisa_de_descuadres():
    data = {n: getattr(__import__(f"budget.{n}", fromlist=["x"]), f"parse_{n}")(2026) for n in ["resumen", "ingresos", "gastos", "inversiones"]}
    assert conv.check_totals(data) == []
    roto = copy.deepcopy(data)
    next(c for c in roto["gastos"]["capitulos"] if c["cap"] == 2)["y2026"] += 500
    avisos = conv.check_totals(roto)
    assert len(avisos) == 1 and "capítulo 2" in avisos[0]
