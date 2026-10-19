"""El build con huellas: todo recurso estático lleva en el nombre el hash de su contenido."""
import json
import os
import re
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
sys.path.insert(0, str(ROOT / "tools"))
import build_site  # noqa: E402

HUELLA = re.compile(r"\.[0-9a-f]{10}\.(css|js|woff2)$")


@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    if os.environ.get("DIST_DIR"):  # el CI comprueba el dist/ que ha construido él mismo
        return Path(os.environ["DIST_DIR"])
    destino = tmp_path_factory.mktemp("dist")
    build_site.build(SITE, destino)
    return destino


def paginas(d):
    return sorted(d.glob("*.html"))


def test_las_doce_paginas_conservan_su_nombre(dist):
    assert [p.name for p in paginas(dist)] == [p.name for p in sorted(SITE.glob("*.html"))]


@pytest.mark.parametrize("nombre", sorted(p.name for p in SITE.glob("*.html")))
def test_los_recursos_de_cada_pagina_existen_y_llevan_huella(dist, nombre):
    html = (dist / nombre).read_text(encoding="utf-8")
    refs = [r for r in re.findall(r'(?:href|src)="([^"]+)"', html) if not r.startswith(("http", "data:", "#"))]
    recursos = [r for r in refs if not r.endswith(".html")]
    assert any(r.endswith(".css") for r in recursos) and any(r.endswith(".js") for r in recursos)
    for ref in recursos:
        assert HUELLA.search(ref), f"{nombre}: {ref} no lleva huella"
        assert (dist / ref).is_file(), f"{nombre}: {ref} no existe"


def test_los_enlaces_a_paginas_html_no_cambian(dist):
    for js in dist.glob("js/*.js"):
        for destino in re.findall(r'href="([a-z]+\.html)', js.read_text(encoding="utf-8")):
            assert (dist / destino).is_file()


def test_los_modulos_importan_ficheros_con_huella_que_existen(dist):
    modulos = list((dist / "js").glob("*.js"))
    assert modulos and not any(m.name.endswith(".test.js") for m in modulos)
    for m in modulos:
        assert HUELLA.search(m.name), m.name
        for spec in re.findall(r'(?:from|import)\s*"(\./[^"]+)"', m.read_text(encoding="utf-8")):
            assert HUELLA.search(spec), f"{m.name} importa {spec} sin huella"
            assert (m.parent / spec).is_file(), f"{m.name} importa {spec}, que no existe"


def test_chart_js_lleva_huella(dist):
    assert [p.name for p in (dist / "vendor").glob("chart.umd.min.*.js")]


def test_los_datos_se_leen_de_la_carpeta_con_huella(dist):
    manifiesto = json.loads((dist / "build-manifest.json").read_text(encoding="utf-8"))
    carpeta = manifiesto["data/"]
    assert re.fullmatch(r"data-[0-9a-f]{10}/", carpeta)
    assert (dist / carpeta / "index.json").is_file()
    assert not (dist / "data").exists()
    for p in paginas(dist):
        assert f'<html lang="es" data-datos="{carpeta}">' in p.read_text(encoding="utf-8"), p.name


def test_solo_data_js_conoce_la_ruta_data():
    for js in (SITE / "js").glob("*.js"):
        if js.name.endswith(".test.js") or js.name == "data.js":
            continue
        assert not re.search(r"[\"'`(]data/", js.read_text(encoding="utf-8")), f"{js.name} construye una ruta data/ a mano"
    assert '"data/"' in (SITE / "js" / "data.js").read_text(encoding="utf-8")


def test_el_manifiesto_relaciona_original_y_fichero_con_huella(dist):
    m = json.loads((dist / "build-manifest.json").read_text(encoding="utf-8"))
    for original in ["css/styles.css", "js/home.js", "js/format.js", "vendor/chart.umd.min.js"]:
        assert (dist / m[original]).is_file()
        assert HUELLA.search(m[original])


def copia_site(tmp_path):
    copia = tmp_path / "site"
    shutil.copytree(SITE, copia)
    return copia


def test_es_reproducible(dist, tmp_path):
    otro = tmp_path / "dist2"
    build_site.build(SITE, otro)
    assert sorted(p.relative_to(dist) for p in dist.rglob("*")) == sorted(p.relative_to(otro) for p in otro.rglob("*"))


def test_cambiar_un_byte_de_format_js_cambia_importadores_y_html(dist, tmp_path):
    copia = copia_site(tmp_path)
    with (copia / "js" / "format.js").open("a", encoding="utf-8") as f:
        f.write("\n// cambio\n")
    nuevo = tmp_path / "dist2"
    build_site.build(copia, nuevo)
    antes = json.loads((dist / "build-manifest.json").read_text(encoding="utf-8"))
    despues = json.loads((nuevo / "build-manifest.json").read_text(encoding="utf-8"))
    importadores = [j for j in (SITE / "js").glob("*.js") if not j.name.endswith(".test.js") and 'from "./format.js"' in j.read_text(encoding="utf-8")]
    assert importadores
    for j in importadores:
        assert antes[f"js/{j.name}"] != despues[f"js/{j.name}"], j.name
    assert antes["js/format.js"] != despues["js/format.js"]
    # ... y los que no lo importan (ni indirectamente) no cambian
    assert antes["css/styles.css"] == despues["css/styles.css"]
    assert antes["data/"] == despues["data/"]
    assert antes["vendor/chart.umd.min.js"] == despues["vendor/chart.umd.min.js"]
    assert (dist / "index.html").read_text() != (nuevo / "index.html").read_text()


def test_cambiar_un_dato_cambia_la_carpeta_y_el_html_no_el_js(dist, tmp_path):
    copia = copia_site(tmp_path)
    with (copia / "data" / "index.json").open("a", encoding="utf-8") as f:
        f.write(" ")
    nuevo = tmp_path / "dist2"
    build_site.build(copia, nuevo)
    antes = json.loads((dist / "build-manifest.json").read_text(encoding="utf-8"))
    despues = json.loads((nuevo / "build-manifest.json").read_text(encoding="utf-8"))
    assert antes["data/"] != despues["data/"]
    assert antes["js/data.js"] == despues["js/data.js"]


def test_los_ciclos_de_importacion_fallan_con_mensaje_claro(tmp_path):
    copia = copia_site(tmp_path)
    (copia / "js" / "a.js").write_text('import "./b.js";\nexport const a = 1;\n', encoding="utf-8")
    (copia / "js" / "b.js").write_text('import { a } from "./a.js";\nexport const b = a;\n', encoding="utf-8")
    with pytest.raises(build_site.CicloDeImportaciones, match=r"a\.js.*b\.js.*a\.js"):
        build_site.build(copia, tmp_path / "dist")


def test_pages_sube_dist_y_comprueba_los_nombres_con_huella():
    pages = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    assert "python tools/build_site.py" in pages and "path: dist" in pages and "path: site" not in pages
    assert "build-manifest.json" in pages


def test_el_ci_construye_dist_y_lo_comprueba():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "python tools/build_site.py" in ci and "DIST_DIR" in ci


def test_el_build_pone_huella_a_las_tipografias_y_reescribe_su_url_en_el_css(tmp_path):
    site = Path(__file__).resolve().parents[2] / "site"
    manifiesto = build_site.build(site, tmp_path / "dist")
    dist = tmp_path / "dist"
    fuentes = [v for k, v in manifiesto.items() if k.startswith("fonts/") and k.endswith(".woff2")]
    assert len(fuentes) == 2 and all(re.search(r"\.[0-9a-f]{10}\.woff2$", f) for f in fuentes)
    css = (dist / manifiesto["css/styles.css"]).read_text(encoding="utf-8")
    urls = re.findall(r"url\(([^)]+)\)", css)
    assert sorted(urls) == sorted("../" + f for f in fuentes)
    for f in fuentes:
        assert (dist / f).is_file()
    index = (dist / "index.html").read_text(encoding="utf-8")
    assert f'href="{manifiesto["fonts/outfit-latin-wght-normal.woff2"]}"' in index


def test_cambiar_una_tipografia_cambia_la_huella_del_css(tmp_path):
    site = tmp_path / "site"
    shutil.copytree(Path(__file__).resolve().parents[2] / "site", site)
    antes = build_site.build(site, tmp_path / "d1")["css/styles.css"]
    fuente = site / "fonts" / "outfit-latin-wght-normal.woff2"
    fuente.write_bytes(fuente.read_bytes() + b"x")
    despues = build_site.build(site, tmp_path / "d2")["css/styles.css"]
    assert antes != despues
