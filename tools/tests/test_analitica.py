"""Analítica con consentimiento: Google solo se carga desde un módulo, tras «Aceptar»; la CSP es la misma en las 12 páginas."""
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
PAGINAS = sorted(SITE.glob("*.html"))
JS = SITE / "js"
FUENTES_JS = [p for p in sorted(JS.glob("*.js")) if not p.name.endswith(".test.js")]
sys.path.insert(0, str(ROOT / "tools"))
import build_site  # noqa: E402

GOOGLE = re.compile(r"googletagmanager|google-analytics|analytics\.google|gtag", re.I)


@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    if os.environ.get("DIST_DIR"):
        return Path(os.environ["DIST_DIR"])
    destino = tmp_path_factory.mktemp("dist")
    build_site.build(SITE, destino)
    return destino


def csp(pagina):
    m = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)">', pagina.read_text(encoding="utf-8"))
    assert m, f"{pagina.name} sin Content-Security-Policy"
    return m.group(1)


def test_hay_doce_paginas_y_todas_con_la_misma_csp():
    assert len(PAGINAS) == 13
    assert len({csp(p) for p in PAGINAS}) == 1, "la CSP debe ser idéntica en todas las páginas"


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_ninguna_pagina_carga_ni_nombra_google_en_el_html_salvo_la_csp(pagina):
    html = pagina.read_text(encoding="utf-8")
    sin_csp = html.replace(csp(pagina), "")
    assert not GOOGLE.search(sin_csp), f"{pagina.name} nombra Google fuera de la CSP"
    assert not re.search(r"<script[^>]+src=\"https?:", html), f"{pagina.name} carga un script externo"


@pytest.mark.parametrize("ruta", FUENTES_JS, ids=lambda p: p.name)
def test_solo_analytics_js_nombra_google_y_solo_el_ID_vive_en_la_configuracion(ruta):
    texto = ruta.read_text(encoding="utf-8")
    if ruta.name == "analytics.js":
        return
    assert not GOOGLE.search(texto), f"{ruta.name} nombra Google"
    if ruta.name != "analytics-config.js":
        assert not re.search(r"G-[A-Z0-9]{8,}", texto), f"{ruta.name} escribe un ID de medición"


def test_analytics_js_es_el_unico_cargador_y_solo_se_llama_tras_el_consentimiento():
    texto = (JS / "analytics.js").read_text(encoding="utf-8")
    assert len(re.findall(r"createElement\(\"script\"\)", texto)) == 1
    assert len(re.findall(r"cargarGa\(win, doc\)", texto)) == 3  # definición + «concedido» guardado + botón «Aceptar»
    for otro in FUENTES_JS:
        if otro.name != "analytics.js":
            assert 'createElement("script")' not in otro.read_text(encoding="utf-8"), f"{otro.name} crea scripts"
    assert "iniciarAnalitica" in (JS / "layout.js").read_text(encoding="utf-8")


def test_el_aviso_y_el_pie_usan_clases_que_existen_en_el_css():
    texto = (JS / "analytics.js").read_text(encoding="utf-8")
    css = (SITE / "css" / "styles.css").read_text(encoding="utf-8")
    clases = set()
    for m in re.finditer(r'class="([^"]+)"', texto):
        clases.update(m.group(1).split())
    assert {"aviso-analitica", "enlace-boton", "pie-privacidad", "boton-primario"} <= clases
    for c in clases:
        assert f".{c}" in css, f"la clase .{c} no tiene reglas en styles.css"
    assert re.search(r"prefers-reduced-motion[^{]*\{[^}]*\.aviso-analitica[^}]*animation:\s*none", css)
    assert re.search(r"\.aviso-analitica\s*\{[^}]*position:\s*fixed", css)
    assert re.search(r"\.aviso-analitica \.boton\s*\{[^}]*min-height:\s*44px", css)


def test_el_build_pone_huella_a_los_modulos_de_analitica_y_los_imports_resuelven(dist):
    manifiesto = (dist / "build-manifest.json").read_text(encoding="utf-8")
    for rel in ("js/analytics.js", "js/analytics-config.js"):
        assert rel in manifiesto
        publicado = re.search(rf'"{re.escape(rel)}": "([^"]+)"', manifiesto).group(1)
        assert re.search(r"\.[0-9a-f]{10}\.js$", publicado) and (dist / publicado).is_file()
    publicados = {p.name for p in (dist / "js").glob("*.js")}
    layout = next(p for p in (dist / "js").glob("layout.*.js"))
    texto = layout.read_text(encoding="utf-8")
    m = re.search(r'from "\./(analytics\.[0-9a-f]{10}\.js)"', texto)
    assert m and m.group(1) in publicados
    analytics = (dist / "js" / m.group(1)).read_text(encoding="utf-8")
    n = re.search(r'from "\./(analytics-config\.[0-9a-f]{10}\.js)"', analytics)
    assert n and n.group(1) in publicados
