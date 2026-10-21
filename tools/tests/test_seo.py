"""SEO: lo que ve un rastreador que no ejecuta JavaScript (HTML estático generado en el build), metadatos y rastreo."""
import html as html_lib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
DOMINIO = "https://presupuestos.arandadeduero.dev/"
sys.path.insert(0, str(ROOT / "tools"))
import build_site  # noqa: E402
import prerender  # noqa: E402
import seo  # noqa: E402

PAGINAS = sorted(p.name for p in SITE.glob("*.html"))  # las de la raíz: portada, alias del último año y páginas sin año
ULTIMO = json.loads((SITE / "data" / "index.json").read_text(encoding="utf-8"))["ultimo"]
ID_DE = {"index.html": "inicio", **{p: p.removesuffix(".html") for p in PAGINAS if p != "index.html"}}


def url_canonica(nombre: str) -> str:
    """Canónica de una página de la raíz: la portada es «/», las que dependen del año apuntan a su carpeta del último año."""
    if nombre == "index.html":
        return DOMINIO
    if ID_DE[nombre] in seo.PAGINAS_ANIO:
        return DOMINIO + f"{ULTIMO}/{nombre}"
    return DOMINIO + nombre


@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    if os.environ.get("DIST_DIR"):  # el CI comprueba el dist/ que ha construido él mismo
        return Path(os.environ["DIST_DIR"])
    destino = tmp_path_factory.mktemp("dist_seo")
    build_site.build(SITE, destino)
    return destino


def leer(dist, nombre):
    return (dist / nombre).read_text(encoding="utf-8")


def texto_visible(html: str) -> str:
    cuerpo = html[html.index("<body>"):]
    cuerpo = re.sub(r"<(script|noscript|template)\b.*?</\1>", " ", cuerpo, flags=re.S)
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", cuerpo))).strip()


def eur(n) -> str:
    return prerender.euros(n).replace("\u00a0", " ")


def url_de(nombre: str) -> str:
    return DOMINIO if nombre == "index.html" else DOMINIO + nombre


def datos(nombre, anio=None):
    indice = json.loads((SITE / "data" / "index.json").read_text(encoding="utf-8"))
    anio = anio or indice["ultimo"]
    return json.loads((SITE / "data" / str(anio) / f"{nombre}.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- contenido sin JS

@pytest.mark.parametrize("nombre", PAGINAS)
def test_cada_pagina_tiene_un_unico_h1_y_ya_no_dice_cargando(dist, nombre):
    html = leer(dist, nombre)
    assert len(re.findall(r"<h1[ >]", html)) == 1
    assert "Cargando" not in html and 'class="cargando' not in html
    assert '<html lang="es"' in html


@pytest.mark.parametrize("nombre", PAGINAS)
def test_cada_pagina_trae_texto_significativo_sin_js(dist, nombre):
    texto = texto_visible(leer(dist, nombre))
    assert len(texto.split()) >= 120, f"{nombre}: solo {len(texto.split())} palabras sin JS"
    assert "<noscript>" in leer(dist, nombre)
    assert "Aranda de Duero" in texto


CLAVES = {
    "index.html": ["Por cada 100", "Personal", "Servicios", "por habitante"],
    "resumen.html": ["Resumen del presupuesto", "Cap 1 - ", "De dónde sale el dinero", "En qué se gasta"],
    "ingresos.html": ["De dónde sale el dinero", "Cap 1 - ", "Cap 9 - "],
    "gastos.html": ["En qué se gasta el dinero", "Cap 6 - ", "Por política de gasto"],
    "inversiones.html": ["Inversiones", "Cómo se pagan", "Remanente de tesorería", "El préstamo es una previsión"],
    "subvenciones.html": ["Subvenciones", "asociaciones y entidades"],
    "deuda.html": ["Deuda del Ayuntamiento", "préstamos", "carga financiera", "31 de diciembre"],
    "comparar.html": ["Comparar presupuestos", "Gasto por habitante"],
    "indicadores.html": ["Nivel de endeudamiento", "Ahorro bruto", "Deuda por habitante"],
    "calculadora.html": ["IBI", "orientativo"],
    "guia.html": ["Presupuesto inicial", "Remanente de tesorería", "Ahorro neto"],
    "metodologia.html": ["Orden EHA/3565/2008", "Orden HAP/419/2014", "INE", "pendientes de que los revise", "incidencia"],
    "descargas.html": ["resumen.json", "deuda.json", ".xlsx"],
}


@pytest.mark.parametrize("nombre", PAGINAS)
def test_las_palabras_clave_de_cada_pagina_estan_en_el_html_estatico(dist, nombre):
    texto = texto_visible(leer(dist, nombre))
    for clave in CLAVES[nombre]:
        assert clave in texto or clave in leer(dist, nombre), f"{nombre}: falta «{clave}»"


def test_las_cifras_estaticas_salen_de_los_json_del_ultimo_anio(dist):
    ultimo = json.loads((SITE / "data" / "index.json").read_text(encoding="utf-8"))["ultimo"]
    r = datos("resumen")
    assert eur(r["totalGastos"]) in texto_visible(leer(dist, "index.html"))
    assert str(ultimo) in texto_visible(leer(dist, "index.html"))
    texto = texto_visible(leer(dist, "resumen.html"))
    assert eur(r["totalIngresos"]) in texto and eur(r["totalGastos"]) in texto
    d = datos("deuda")
    assert eur(d["titular"]["vivaFin"]) in texto_visible(leer(dist, "deuda.html"))
    i = datos("inversiones")
    assert eur(i["total"]) in texto_visible(leer(dist, "inversiones.html"))
    s = datos("subvenciones")
    assert eur(s["total"]) in texto_visible(leer(dist, "subvenciones.html"))
    for c in datos("ingresos")["capitulos"]:
        assert f"Cap {c['cap']} - {c['corto']}" in texto_visible(leer(dist, "ingresos.html"))
    for c in datos("gastos")["capitulos"]:
        assert f"Cap {c['cap']} - {c['corto']}" in texto_visible(leer(dist, "gastos.html"))


def test_el_aviso_del_prestamo_es_el_mismo_texto_que_pinta_el_js(dist):
    # No se copia a Python: lo exporta el propio módulo del JS
    js = prerender.exportar_js(SITE, "img/escudo.png", "2026-01-01")
    for pagina, clave in [("deuda.html", "deuda"), ("inversiones.html", "inversiones")]:
        assert js["entornos"]["raiz"]["avisos"][clave] in leer(dist, pagina)


def test_la_guia_estatica_tiene_todos_los_terminos_con_las_mismas_anclas_que_el_js(dist):
    terminos = json.loads((SITE / "data" / "guia-terminos.json").read_text(encoding="utf-8"))
    html = leer(dist, "guia.html")
    for t in terminos:
        assert f'<dt id="{prerender.id_termino(t["termino"])}">{html_lib.escape(t["termino"], quote=True)}</dt>' in html
    ids_js = subprocess.run(
        ["node", "--input-type=module", "-e", f'import {{ idTermino }} from "{(SITE / "js" / "format.js").as_uri()}";'
         f"console.log(JSON.stringify({json.dumps([t['termino'] for t in terminos], ensure_ascii=False)}.map(idTermino)));"],
        capture_output=True, text=True, check=True).stdout
    assert json.loads(ids_js) == [prerender.id_termino(t["termino"]) for t in terminos]


def test_descargas_enlaza_los_json_con_huella_y_los_excel_originales(dist):
    html = leer(dist, "descargas.html")
    carpeta = json.loads(leer(dist, "build-manifest.json"))["data/"]
    indice = json.loads((SITE / "data" / "index.json").read_text(encoding="utf-8"))
    for a in indice["anios"]:
        for f in ["resumen", "ingresos", "gastos", "inversiones", "subvenciones", "deuda"]:
            assert f'href="{carpeta}{a["anio"]}/{f}.json"' in html
            assert (dist / carpeta / str(a["anio"]) / f"{f}.json").is_file()
        for x in (ROOT / str(a["anio"])).glob("*.xlsx"):
            assert f"https://github.com/arandadeduero/visorpresupuesto/raw/main/{a['anio']}/" in html
            assert prerender.url_excel(a["anio"], x.name).replace("&", "&amp;") in html


# ---------------------------------------------------------------- metadatos

def meta(html, nombre):
    m = re.search(rf'<meta name="{nombre}" content="([^"]*)"', html)
    return html_lib.unescape(m.group(1)) if m else None


@pytest.fixture(scope="module")
def cabeceras(dist):
    salida = {}
    for n in PAGINAS:
        h = leer(dist, n)
        salida[n] = {
            "titulo": html_lib.unescape(re.search(r"<title>(.*?)</title>", h).group(1)),
            "descripcion": meta(h, "description"),
            "canonical": re.findall(r'<link rel="canonical" href="([^"]+)"', h),
        }
    return salida


def test_titulos_y_descripciones_cumplen_longitud_y_son_unicos(cabeceras):
    for n, c in cabeceras.items():
        assert 0 < len(c["titulo"]) <= 60, f"{n}: título de {len(c['titulo'])}"
        assert 120 <= len(c["descripcion"]) <= 160, f"{n}: descripción de {len(c['descripcion'])}"
    assert len({c["titulo"] for c in cabeceras.values()}) == len(PAGINAS)
    assert len({c["descripcion"] for c in cabeceras.values()}) == len(PAGINAS)


def test_los_titulos_de_la_raiz_son_los_pedidos(cabeceras):
    """La portada y las páginas sin año tienen título propio; los alias del último año, el de su página en /<último año>/."""
    esperados = {
        "index.html": "Presupuesto de Aranda de Duero: en qué se gasta",
        "comparar.html": "Comparar presupuestos de Aranda de Duero entre años",
        "guia.html": "Guía del presupuesto municipal: capítulos y partidas",
        "descargas.html": "Datos abiertos del presupuesto de Aranda de Duero",
        "metodologia.html": "Metodología y fuentes de los datos de Aranda de Duero",
    }
    esperados |= {f"{i}.html": seo.textos_anio(i, ULTIMO)[0] for i in seo.PAGINAS_ANIO if i != "inicio"}
    for n, t in esperados.items():
        assert cabeceras[n]["titulo"] == t


@pytest.mark.parametrize("nombre", PAGINAS)
def test_la_url_canonica_es_absoluta_unica_y_sin_parametros(cabeceras, nombre):
    assert cabeceras[nombre]["canonical"] == [url_canonica(nombre)]
    assert "?" not in cabeceras[nombre]["canonical"][0]


# ---------------------------------------------------------------- rastreo

def test_el_sitemap_tiene_lastmod_y_no_lista_alias(dist):
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    raiz = ET.fromstring(leer(dist, "sitemap.xml"))
    urls = {e.find("s:loc", ns).text: e.find("s:lastmod", ns) for e in raiz.findall("s:url", ns)}
    assert url_de("index.html") in urls and url_de("metodologia.html") in urls
    for n in PAGINAS:  # los alias de la raíz tienen la canónica en otra URL: no se listan
        assert (url_de(n) in urls) == (url_canonica(n) == url_de(n)), n
    for u, lastmod in urls.items():
        assert lastmod is not None and re.fullmatch(r"\d{4}-\d{2}-\d{2}", lastmod.text), u


def test_robots_apunta_al_sitemap(dist):
    robots = leer(dist, "robots.txt")
    assert "User-agent: *" in robots and f"Sitemap: {DOMINIO}sitemap.xml" in robots


def test_la_404_esta_marcada_noindex_sin_canonical_y_con_enlaces_rastreables(dist):
    html = leer(dist, "404.html")
    assert '<meta name="robots" content="noindex">' in html
    assert "canonical" not in html and "og:url" not in html
    for n in PAGINAS:  # los enlaces de la 404 van a la URL canónica de cada página
        assert f'href="{url_canonica(n).removeprefix(DOMINIO.rstrip("/"))}"' in html, n
    # sirve en cualquier ruta: nada relativo
    for ref in re.findall(r'(?:href|src)="([^"]+)"', html):
        assert ref.startswith(("/", "http", "#", "data:")), ref
    assert "<h1>Página no encontrada</h1>" in html and "<noscript>" not in html


def hrefs_internos(html):
    for ref in re.findall(r'(?:href|src)="([^"]+)"', html):
        if ref.startswith(("http", "data:", "#", "mailto:")):
            continue
        yield ref


@pytest.mark.parametrize("nombre", PAGINAS)
def test_los_enlaces_internos_existen_y_la_portada_se_enlaza_como_barra(dist, nombre):
    html = leer(dist, nombre)
    for ref in hrefs_internos(html):
        ruta = re.split(r"[?#]", ref)[0]
        assert ruta != "index.html", f"{nombre}: enlaza index.html en vez de ./"
        assert (dist / ("index.html" if ruta in ("", "./") else ruta + "index.html" if ruta.endswith("/") else ruta)).is_file(), f"{nombre}: {ref} no existe"
    assert 'href="./"' in html  # logo y menú


def test_el_pie_lleva_los_enlaces_institucionales(dist):
    for n in PAGINAS:
        html = leer(dist, n)
        for url in ["https://www.arandadeduero.es\"", "https://transparencia.arandadeduero.es\"", "https://github.com/arandadeduero/visorpresupuesto\"",
                    "https://www.arandadeduero.es/politica-privacidad/\"", 'href="metodologia.html"']:
            assert url in html, f"{n}: falta {url}"
        assert re.search(r"Datos actualizados el \d{1,2} de \w+ de \d{4}", html)
        assert re.search(r'<html lang="es" [^>]*data-actualizado="\d{4}-\d{2}-\d{2}"', html)


@pytest.mark.parametrize("nombre", [n for n in PAGINAS if n not in ("guia.html", "metodologia.html", "descargas.html", "calculadora.html", "index.html")])
def test_las_paginas_de_datos_enlazan_a_otras_con_anclas_descriptivas(dist, nombre):
    html = leer(dist, nombre)
    bloque = re.search(r'<nav class="relacionado".*?</nav>', html, re.S)
    assert bloque, f"{nombre}: sin «Relacionado»"
    anclas = re.findall(r"<a [^>]*>(.*?)</a>", bloque.group(0))
    assert len(anclas) >= 3 and all(len(a.split()) >= 3 for a in anclas)
    assert "Ver más" not in html and "→" not in re.sub(r"<script.*?</script>", "", html, flags=re.S)


def test_la_portada_usa_anclas_descriptivas(dist):
    html = leer(dist, "index.html")
    assert "Ver más" not in html
    for ancla in ["Deuda del Ayuntamiento", "Inversiones previstas", "Indicadores de endeudamiento", "Calculadora de impuestos"]:
        assert f"<strong>{ancla}</strong>" in html


# ---------------------------------------------------------------- reglas del proyecto sobre el HTML generado

@pytest.mark.parametrize("nombre", PAGINAS + ["404.html"])
def test_el_html_generado_no_lleva_estilos_en_linea_ni_colores_ni_scripts_en_linea(dist, nombre):
    html = leer(dist, nombre)
    assert not re.search(r"\sstyle\s*=", html, re.I) and "<style" not in html.lower()
    # el bloque application/ld+json es de datos, no se ejecuta (ver test_jsonld.py)
    assert not re.search(r"<script(?![^>]*\bsrc=)(?![^>]*application/ld\+json)[^>]*>", html)
    assert not re.search(r"#[0-9a-fA-F]{6}\b", re.sub(r'<meta name="theme-color"[^>]*>', "", html))
    csp = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)">', html).group(1)
    assert "'unsafe-inline'" not in csp and "style-src 'self';" in csp
    assert "script-src 'self' https://www.googletagmanager.com;" in csp


def test_el_html_fuente_sigue_funcionando_en_local_con_cargando():
    for n in PAGINAS:
        assert 'class="cargando wrap"' in (SITE / n).read_text(encoding="utf-8")


def test_los_titulos_del_js_parten_del_titulo_estatico():
    layout = (SITE / "js" / "layout.js").read_text(encoding="utf-8")
    assert "document.title = `${tituloEstatico} (${anio})`" in layout


def test_las_etiquetas_de_los_indicadores_coinciden_con_las_de_indicadores_js(dist):
    js = (SITE / "js" / "indicadores.js").read_text(encoding="utf-8")
    titulos = re.findall(r'titulo: "([^"]+)"', js)
    assert len(titulos) == 7
    texto = texto_visible(leer(dist, "indicadores.html"))
    for t in titulos:
        assert t in texto, t
