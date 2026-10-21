"""Licencia de los datos: Creative Commons Reconocimiento 4.0 (CC BY 4.0). El código sigue siendo MIT."""
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
    fuente = (SITE / "js" / "descargas.js").read_text(encoding="utf-8")
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
