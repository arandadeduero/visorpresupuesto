"""Integridad de la web publicada: enlaces locales, módulos JS, datos por año y flujo de GitHub Actions."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
PAGINAS = sorted(SITE.glob("*.html"))


def test_hay_siete_paginas():
    assert [p.name for p in PAGINAS] == ["deuda.html", "gastos.html", "index.html", "ingresos.html", "inversiones.html", "resumen.html", "subvenciones.html"]


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_los_recursos_locales_de_cada_pagina_existen(pagina):
    html = pagina.read_text(encoding="utf-8")
    refs = re.findall(r'(?:href|src)="([^"]+)"', html)
    locales = [r for r in refs if not r.startswith(("http", "data:", "#"))]
    assert locales, "la página no enlaza ni css ni js"
    for ref in locales:
        assert "/" != ref[0], f"ruta absoluta: {ref}"
        assert (SITE / ref).is_file(), f"{pagina.name} enlaza {ref}, que no existe"


def test_los_imports_de_los_modulos_js_existen():
    for js in (SITE / "js").glob("*.js"):
        for spec in re.findall(r'from "(\./[^"]+)"', js.read_text(encoding="utf-8")):
            assert (js.parent / spec).is_file(), f"{js.name} importa {spec}, que no existe"


def test_cada_anio_del_indice_tiene_sus_seis_ficheros_de_datos():
    indice = json.loads((SITE / "data" / "index.json").read_text(encoding="utf-8"))
    assert indice["ultimo"] == max(a["anio"] for a in indice["anios"])
    for a in indice["anios"]:
        for nombre in ["resumen", "ingresos", "gastos", "inversiones", "subvenciones", "deuda"]:
            ruta = SITE / "data" / str(a["anio"]) / f"{nombre}.json"
            assert json.loads(ruta.read_text(encoding="utf-8"))["anio"] == a["anio"], ruta


def test_las_paginas_con_graficos_cargan_chart_js_antes_de_su_modulo():
    for nombre in ["deuda", "resumen", "ingresos", "gastos"]:
        html = (SITE / f"{nombre}.html").read_text(encoding="utf-8")
        assert html.index("vendor/chart.umd.min.js") < html.index('type="module"'), nombre


def _workflow(nombre):
    return (ROOT / ".github" / "workflows" / nombre).read_text(encoding="utf-8")


def test_el_despliegue_espera_a_los_tests_y_no_se_cancela_a_medias():
    pages = _workflow("pages.yml")
    assert "branches: [main]" in pages
    assert re.search(r"deploy:\s*\n\s*needs:\s*test", pages)
    assert "cancel-in-progress: false" in pages
    assert "uses: ./.github/workflows/ci.yml" in pages


def test_el_ci_se_ejecuta_en_pull_requests_y_comprueba_los_datos_generados():
    ci = _workflow("ci.yml")
    assert "pull_request:" in ci and "workflow_call:" in ci
    assert "pytest" in ci and "node --test \"site/js/*.test.js\"" in ci
    assert "git diff --exit-code site/data" in ci


def test_tras_desplegar_se_comprueba_que_la_web_carga():
    pages = _workflow("pages.yml")
    assert "page_url" in pages and "curl" in pages and "Presupuestos de Aranda de Duero" in pages
