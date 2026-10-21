"""Logo, metadatos para redes sociales, iconos, manifiesto, robots y sitemap."""
import html as html_lib
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
IMG = SITE / "img"
PAGINAS = sorted(SITE.glob("*.html"))
DOMINIO = "https://presupuestos.arandadeduero.dev/"
sys.path.insert(0, str(ROOT / "tools"))
import build_site  # noqa: E402


def metas(texto: str) -> dict:
    """name/property -> content de todas las <meta> con contenido."""
    salida = {}
    for m in re.finditer(r"<meta\s+(?:name|property)=\"([^\"]+)\"\s+content=\"([^\"]*)\"\s*>", texto):
        salida.setdefault(m.group(1), html_lib.unescape(m.group(2)))
    return salida


def datos(pagina: Path):
    texto = pagina.read_text(encoding="utf-8")
    return texto, metas(texto), html_lib.unescape(re.search(r"<title>(.*?)</title>", texto).group(1))


def url_pagina(pagina: Path) -> str:
    return DOMINIO if pagina.name == "index.html" else DOMINIO + pagina.name


def dimensiones_png(ruta: Path) -> tuple[int, int]:
    cab = ruta.read_bytes()[:24]
    assert cab[:8] == b"\x89PNG\r\n\x1a\n", f"{ruta.name} no es PNG"
    return struct.unpack(">II", cab[16:24])


ETIQUETAS_OG = ["og:type", "og:site_name", "og:locale", "og:title", "og:description", "og:url", "og:image",
                "og:image:width", "og:image:height", "og:image:type", "og:image:alt"]
ETIQUETAS_TW = ["twitter:card", "twitter:title", "twitter:description", "twitter:image", "twitter:image:alt"]


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_cada_pagina_tiene_descripcion_canonica_open_graph_y_twitter(pagina):
    texto, m, titulo = datos(pagina)
    assert 0 < len(m.get("description", "")) <= 160
    assert 0 < len(titulo) <= 70
    assert f'<link rel="canonical" href="{url_pagina(pagina)}">' in texto
    for e in ETIQUETAS_OG + ETIQUETAS_TW:
        assert m.get(e), f"{pagina.name}: falta {e}"
    assert m["og:type"] == "website" and m["og:locale"] == "es_ES"
    assert m["og:site_name"] == "Presupuestos de Aranda de Duero"
    assert m["og:title"] == titulo == m["twitter:title"]
    assert m["og:description"] == m["description"] == m["twitter:description"]
    assert m["og:url"] == url_pagina(pagina)
    assert m["twitter:card"] == "summary_large_image"
    assert m["og:image"] == m["twitter:image"] == DOMINIO + "img/social.png"
    assert (m["og:image:width"], m["og:image:height"], m["og:image:type"]) == ("1200", "630", "image/png")
    assert m["og:image:alt"] == m["twitter:image:alt"]


def test_titulos_y_descripciones_son_unicos():
    todos = [datos(p) for p in PAGINAS]
    assert len({t for _, _, t in todos}) == len(PAGINAS)
    assert len({m["description"] for _, m, _ in todos}) == len(PAGINAS)


def test_las_descripciones_no_llevan_cifras_que_se_queden_obsoletas():
    for p in PAGINAS:
        # solo vale «100 €» (el «por cada 100 €» de la portada, que no caduca)
        assert not re.search(r"\d", datos(p)[1]["description"].replace("100 €", "")), p.name


def test_la_imagen_social_es_1200x630_y_ligera():
    ruta = IMG / "social.png"
    assert dimensiones_png(ruta) == (1200, 630)
    assert ruta.stat().st_size < 300_000


ICONOS = {"favicon-32.png": (32, 32), "apple-touch-icon.png": (180, 180), "icon-192.png": (192, 192), "icon-512.png": (512, 512)}


@pytest.mark.parametrize("nombre,tam", ICONOS.items())
def test_los_iconos_existen_con_su_tamano(nombre, tam):
    assert dimensiones_png(IMG / nombre) == tam


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_cada_pagina_enlaza_favicon_apple_touch_y_manifiesto(pagina):
    texto = pagina.read_text(encoding="utf-8")
    assert '<link rel="icon" href="img/favicon-32.png" type="image/png" sizes="32x32">' in texto
    assert '<link rel="apple-touch-icon" href="img/apple-touch-icon.png" sizes="180x180">' in texto
    assert '<link rel="manifest" href="manifest.webmanifest">' in texto
    assert "data:," not in texto
    # Los dos colores de tema siguen ahí
    assert texto.count('<meta name="theme-color"') == 2


def test_el_manifiesto_es_valido_y_sus_iconos_existen():
    m = json.loads((SITE / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert m["name"] == "Presupuestos de Aranda de Duero" and m["short_name"] and m["lang"] == "es"
    assert m["display"] in ("standalone", "browser") and m["start_url"] == "./"
    assert re.fullmatch(r"#[0-9a-f]{6}", m["theme_color"]) and re.fullmatch(r"#[0-9a-f]{6}", m["background_color"])
    tamanos = set()
    for i in m["icons"]:
        w, h = map(int, i["sizes"].split("x"))
        assert dimensiones_png(SITE / i["src"]) == (w, h) and i["type"] == "image/png"
        tamanos.add(w)
    assert {192, 512} <= tamanos


def test_robots_apunta_al_sitemap_que_genera_el_build():
    # El sitemap.xml lo genera tools/build_site.py (con lastmod); sus pruebas están en test_seo.py
    robots = (SITE / "robots.txt").read_text(encoding="utf-8")
    assert "User-agent: *" in robots and f"Sitemap: {DOMINIO}sitemap.xml" in robots
    assert not (SITE / "sitemap.xml").exists()


def test_el_logo_de_la_cabecera_tiene_alt_tamano_y_enlaza_a_la_portada():
    js = (SITE / "js" / "layout.js").read_text(encoding="utf-8")
    m = re.search(r'<a class="marca" href="\./\$\{consulta\}">(<img [^>]*>)', js)
    assert m, "el logo debe ir dentro del enlace de la marca"
    img = m.group(1)
    assert 'alt="Ayuntamiento de Aranda de Duero"' in img
    ancho = int(re.search(r'width="(\d+)"', img).group(1))
    alto = int(re.search(r'height="(\d+)"', img).group(1))
    real = dimensiones_png(IMG / "escudo.png")
    assert abs(ancho / alto - real[0] / real[1]) < 0.03 and real[0] >= 2 * ancho  # nítido en pantallas 2x
    assert "style" not in img


def test_hay_readme_de_las_imagenes_con_su_origen():
    t = (IMG / "README.md").read_text(encoding="utf-8")
    assert "arandadeduero.es" in t and "propiedad del Ayuntamiento" in t


# --- El build ---

@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    destino = tmp_path_factory.mktemp("dist_img")
    build_site.build(SITE, destino)
    return destino


def test_el_build_mantiene_estables_la_imagen_social_y_los_iconos(dist):
    for nombre in ["social.png", *ICONOS]:
        assert (dist / "img" / nombre).read_bytes() == (IMG / nombre).read_bytes()
    for f in ["manifest.webmanifest", "robots.txt", "sitemap.xml"]:
        assert (dist / f).is_file()


def test_el_build_pone_huella_al_escudo_de_la_cabecera_y_lo_anota_en_cada_html(dist):
    publicados = [p.name for p in (dist / "img").glob("escudo.*.png")]
    assert len(publicados) == 1 and re.fullmatch(r"escudo\.[0-9a-f]{10}\.png", publicados[0])
    assert not (dist / "img" / "escudo.png").exists()
    for p in PAGINAS:
        assert f'data-escudo="img/{publicados[0]}"' in (dist / p.name).read_text(encoding="utf-8")


def test_el_build_no_deja_estilos_en_linea_en_las_paginas(dist):
    for p in dist.glob("*.html"):
        assert "style=" not in p.read_text(encoding="utf-8")
