"""Licencias: datos con Creative Commons Reconocimiento 4.0 (CC BY 4.0) y código con la EUPL v1.2 (la común del Ayuntamiento)."""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
URL = "https://creativecommons.org/licenses/by/4.0/"
sys.path.insert(0, str(ROOT / "tools"))
import build_site  # noqa: E402


@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    destino = tmp_path_factory.mktemp("dist")
    build_site.build(SITE, destino)
    return destino


def _jsonld(html):
    bloques = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    return [json.loads(b) for b in bloques]


def _nodos(html):
    salida = []
    for b in _jsonld(html):
        salida += b["@graph"] if isinstance(b, dict) and "@graph" in b else [b]
    return salida


def test_cada_dataset_declara_la_licencia_y_la_atribucion(dist):
    datasets = [n for n in _nodos((dist / "descargas.html").read_text(encoding="utf-8")) if n.get("@type") == "Dataset"]
    assert len(datasets) >= 3
    for d in datasets:
        assert d["license"] == URL, d["name"]
        assert d["creditText"] == "Ayuntamiento de Aranda de Duero"


def test_descargas_explica_la_licencia_y_como_citar(dist):
    html = (dist / "descargas.html").read_text(encoding="utf-8")
    assert "CC BY 4.0" in html and URL in html
    assert "Fuente: Ayuntamiento de Aranda de Duero" in html


def test_la_licencia_tambien_sale_al_ejecutar_el_js():
    fuente = (SITE / "js" / "descargas-html.js").read_text(encoding="utf-8")  # lo que pinta descargas.js
    assert "CC BY 4.0" in fuente and URL in fuente


def test_el_pie_de_todas_las_paginas_menciona_la_licencia(dist):
    paginas = [p for p in dist.rglob("*.html") if p.name != "404.html"]
    assert len(paginas) > 30
    for p in paginas:
        assert "CC BY 4.0" in p.read_text(encoding="utf-8"), p.relative_to(dist)


def test_metodologia_tiene_apartado_de_licencia(dist):
    html = (dist / "metodologia.html").read_text(encoding="utf-8")
    assert re.search(r"<h2>Licencia[^<]*</h2>", html) and "CC BY 4.0" in html


def test_readme_y_fichero_de_licencia_de_datos():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    seccion = readme[readme.index("## Licencia"):]
    assert "MIT" in seccion and "CC BY 4.0" in seccion and URL in seccion
    datos = (ROOT / "LICENSE-DATOS.md").read_text(encoding="utf-8")
    assert "Creative Commons" in datos and URL in datos and "Ayuntamiento de Aranda de Duero" in datos


EUPL = "https://interoperable-europe.ec.europa.eu/collection/eupl/eupl-text-eupl-12"


def test_el_codigo_es_eupl_en_el_repositorio_y_en_la_web(dist):
    assert "EUROPEAN UNION PUBLIC LICENCE v. 1.2" in (ROOT / "LICENSE").read_text(encoding="utf-8")
    for doc in [ROOT / "LICENSE-DATOS.md", SITE / "metodologia.html", SITE / "js" / "layout.js"]:
        texto = doc.read_text(encoding="utf-8")
        assert "MIT" not in texto, f"{doc.name} aún dice MIT"
        assert "EUPL" in texto, doc.name
    for pagina in ["index.html", "metodologia.html"]:
        assert EUPL in (dist / pagina).read_text(encoding="utf-8"), pagina
