"""Una URL propia e indexable por año (/2025/gastos.html): estructura, SEO de cada año, rutas relativas con profundidad y sitemap."""
import html as html_lib
import json
import os
import re
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

INDICE = json.loads((SITE / "data" / "index.json").read_text(encoding="utf-8"))
ANIOS = [a["anio"] for a in INDICE["anios"]]
ULTIMO = INDICE["ultimo"]
IDS_ANIO = seo.PAGINAS_ANIO  # inicio, resumen, ..., calculadora
SIN_ANIO = ["comparar", "guia", "metodologia", "descargas"]
ALIAS = [f"{i}.html" for i in IDS_ANIO if i != "inicio"]  # páginas de la raíz que son el último año
RAIZ = ["index.html"] + ALIAS + [f"{i}.html" for i in SIN_ANIO]


def ruta(id_: str, anio: int) -> str:
    return f"{anio}/index.html" if id_ == "inicio" else f"{anio}/{id_}.html"


PAGINAS_ANIO = [ruta(i, a) for a in ANIOS for i in IDS_ANIO]
TODAS = PAGINAS_ANIO + RAIZ


@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    if os.environ.get("DIST_DIR"):  # el CI comprueba el dist/ que ha construido él mismo
        return Path(os.environ["DIST_DIR"])
    destino = tmp_path_factory.mktemp("dist_anios")
    build_site.build(SITE, destino)
    return destino


def leer(dist, nombre):
    return (dist / nombre).read_text(encoding="utf-8")


def url_de(nombre: str) -> str:
    """URL absoluta de un fichero de dist/ (las portadas son carpetas)."""
    return DOMINIO + nombre.removesuffix("index.html")


def canonica_esperada(nombre: str) -> str:
    """Reglas de canonical: la portada «/» (también /<último año>/), cada año en su carpeta, los alias del último año en su carpeta."""
    if nombre in ("index.html", f"{ULTIMO}/index.html"):
        return DOMINIO
    if nombre in ALIAS:
        return DOMINIO + f"{ULTIMO}/{nombre}"
    return url_de(nombre)


def meta(html, nombre):
    m = re.search(rf'<meta name="{nombre}" content="([^"]*)"', html)
    return html_lib.unescape(m.group(1)) if m else None


def titulo(html):
    return html_lib.unescape(re.search(r"<title>(.*?)</title>", html).group(1))


def texto_visible(html: str) -> str:
    cuerpo = html[html.index("<body>"):]
    cuerpo = re.sub(r"<(script|noscript|template)\b.*?</\1>", " ", cuerpo, flags=re.S)
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", cuerpo))).strip()


def eur(n) -> str:
    return prerender.euros(n).replace(" ", " ")


def datos(nombre, anio):
    return json.loads((SITE / "data" / str(anio) / f"{nombre}.json").read_text(encoding="utf-8"))


def nodos(html):
    salida = []
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        salida += json.loads(b)["@graph"]
    return salida


# ---------------------------------------------------------------- estructura

def test_los_anios_salen_del_indice_y_hay_tres():
    assert ANIOS == [2024, 2025, 2026] and ULTIMO == 2026


def test_existen_las_paginas_de_cada_anio_las_de_la_raiz_y_la_404(dist):
    assert len(PAGINAS_ANIO) == len(ANIOS) * 9 == 27
    for n in TODAS + ["404.html", "sitemap.xml", "robots.txt"]:
        assert (dist / n).is_file(), n
    assert len(RAIZ) == 13  # portada, 8 alias del último año y comparar, guía, metodología y descargas
    carpetas = sorted(p.name for p in dist.iterdir() if p.is_dir() and re.fullmatch(r"\d{4}", p.name))
    assert carpetas == [str(a) for a in ANIOS]
    for a in ANIOS:
        assert sorted(p.name for p in (dist / str(a)).iterdir()) == sorted(["index.html"] + [f"{i}.html" for i in IDS_ANIO if i != "inicio"])


def test_las_paginas_sin_año_no_tienen_carpeta_de_año(dist):
    for i in SIN_ANIO:
        for a in ANIOS:
            assert not (dist / str(a) / f"{i}.html").exists()


# ---------------------------------------------------------------- SEO de cada página

@pytest.mark.parametrize("nombre", TODAS)
def test_idioma_y_un_solo_h1(dist, nombre):
    html = leer(dist, nombre)
    assert '<html lang="es"' in html
    assert len(re.findall(r"<h1[ >]", html)) == 1 and "Cargando" not in html


@pytest.mark.parametrize("nombre", PAGINAS_ANIO)
def test_el_h1_de_una_pagina_de_anio_lleva_el_anio(dist, nombre):
    anio = nombre.split("/")[0]
    h1 = re.sub(r"<[^>]+>", " ", re.search(r"<h1[^>]*>(.*?)</h1>", leer(dist, nombre), re.S).group(1))
    assert anio in h1, f"{nombre}: {h1}"


@pytest.mark.parametrize("nombre", PAGINAS_ANIO)
def test_titulo_descripcion_y_og_de_cada_pagina_de_anio(dist, nombre):
    anio, resto = nombre.split("/")
    id_ = "inicio" if resto == "index.html" else resto.removesuffix(".html")
    html = leer(dist, nombre)
    t, d = seo.textos_anio(id_, int(anio))
    assert titulo(html) == t and anio in t
    assert meta(html, "description") == d and anio in d
    assert not re.search(r"\d{1,3}(?:\.\d{3})+|\d+,\d+ ?M", d), "la descripción no lleva cifras"
    assert 0 < len(t) <= 60 and 120 <= len(d) <= 160, (len(t), len(d))
    canonica = canonica_esperada(nombre)
    assert re.findall(r'<link rel="canonical" href="([^"]+)"', html) == [canonica]
    assert f'<meta property="og:url" content="{canonica}">' in html
    assert f'<meta property="og:title" content="{html_lib.escape(t)}">' in html
    assert f'<meta name="twitter:title" content="{html_lib.escape(t)}">' in html
    assert f'<meta property="og:description" content="{html_lib.escape(d)}">' in html


def test_titulos_y_descripciones_son_unicos_entre_las_paginas_indexables(dist):
    """Las páginas indexables son las que tienen su propia canónica (no los alias ni /<último año>/, que son la portada)."""
    titulos, descripciones = [], []
    for n in TODAS:
        if canonica_esperada(n) != url_de(n):
            continue
        h = leer(dist, n)
        titulos.append(titulo(h))
        descripciones.append(meta(h, "description"))
        assert 0 < len(titulos[-1]) <= 60 and 120 <= len(descripciones[-1]) <= 160, n
    assert len(titulos) == 1 + 2 * 1 + 3 * 8 + 4  # portada, portadas de los otros años, 8 páginas por año y 4 sin año
    assert len(set(titulos)) == len(titulos) and len(set(descripciones)) == len(descripciones)


@pytest.mark.parametrize("nombre", ALIAS)
def test_los_alias_de_la_raiz_son_la_pagina_del_ultimo_anio_con_canonica_en_su_carpeta(dist, nombre):
    alias, anio = leer(dist, nombre), leer(dist, f"{ULTIMO}/{nombre}")
    assert re.findall(r'<link rel="canonical" href="([^"]+)"', alias) == [DOMINIO + f"{ULTIMO}/{nombre}"]
    assert titulo(alias) == titulo(anio)
    assert texto_visible(alias) == texto_visible(anio).replace("Otros años", "Otros años")  # mismo contenido


def test_la_portada_es_la_raiz_y_la_carpeta_del_ultimo_anio_apunta_a_ella(dist):
    assert re.findall(r'<link rel="canonical" href="([^"]+)"', leer(dist, "index.html")) == [DOMINIO]
    assert re.findall(r'<link rel="canonical" href="([^"]+)"', leer(dist, f"{ULTIMO}/index.html")) == [DOMINIO]
    for a in ANIOS:
        if a != ULTIMO:
            assert re.findall(r'<link rel="canonical" href="([^"]+)"', leer(dist, f"{a}/index.html")) == [f"{DOMINIO}{a}/"]


@pytest.mark.parametrize("nombre", [ruta(i, a) for a in ANIOS for i in IDS_ANIO if i != "inicio"])
def test_migas_de_pan_con_el_anio(dist, nombre):
    anio, resto = nombre.split("/")
    migas = [n for n in nodos(leer(dist, nombre)) if n["@type"] == "BreadcrumbList"]
    assert len(migas) == 1
    items = migas[0]["itemListElement"]
    assert [i["position"] for i in items] == [1, 2, 3]
    assert [i["item"] for i in items] == [DOMINIO, f"{DOMINIO}{anio}/", DOMINIO + nombre]
    assert items[1]["name"] == f"Presupuesto {anio}"


def test_la_portada_de_un_anio_lleva_migas_con_dos_niveles(dist):
    migas = next(n for n in nodos(leer(dist, "2025/index.html")) if n["@type"] == "BreadcrumbList")
    assert [i["item"] for i in migas["itemListElement"]] == [DOMINIO, DOMINIO + "2025/"]


def test_la_raiz_sigue_teniendo_web_y_organizacion_y_descargas_los_datasets(dist):
    assert {"WebSite", "GovernmentOrganization"} <= {n["@type"] for n in nodos(leer(dist, "index.html"))}
    datasets = [n for n in nodos(leer(dist, "descargas.html")) if n["@type"] == "Dataset"]
    assert [d["temporalCoverage"] for d in datasets] == [str(a) for a in ANIOS]


# ---------------------------------------------------------------- contenido sin JavaScript, del año de la página

def test_cada_pagina_de_anio_trae_las_cifras_de_su_anio_y_no_las_del_ultimo(dist):
    for a in ANIOS:
        resumen, gastos, deuda = datos("resumen", a), datos("gastos", a), datos("deuda", a)
        total_gastos = sum(c["actual"] for c in gastos["capitulos"])
        t = texto_visible(leer(dist, f"{a}/gastos.html"))
        assert eur(total_gastos) in t
        assert eur(resumen["totalGastos"]) in texto_visible(leer(dist, f"{a}/resumen.html"))
        assert eur(resumen["totalGastos"]) in texto_visible(leer(dist, f"{a}/index.html"))
        assert eur(deuda["titular"]["vivaFin"]) in texto_visible(leer(dist, f"{a}/deuda.html"))
        assert eur(datos("inversiones", a)["total"]) in texto_visible(leer(dist, f"{a}/inversiones.html"))
        assert eur(datos("subvenciones", a)["total"]) in texto_visible(leer(dist, f"{a}/subvenciones.html"))
        for otro in ANIOS:
            if otro != a:
                assert eur(sum(c["actual"] for c in datos("gastos", otro)["capitulos"])) not in t, f"/{a}/gastos.html trae cifras de {otro}"
        assert f"{a}" in t


def test_2025_gastos_no_trae_los_datos_de_2026(dist):
    t = texto_visible(leer(dist, "2025/gastos.html"))
    assert eur(sum(c["actual"] for c in datos("gastos", 2025)["capitulos"])) in t
    assert eur(sum(c["actual"] for c in datos("gastos", 2026)["capitulos"])) not in t


def test_la_deuda_de_2024_no_cuenta_con_prestamo_previsto(dist):
    html = leer(dist, "2024/deuda.html")
    assert "Previsión: un préstamo nuevo" not in html and "Préstamos previstos en los ingresos" in html
    assert "Previsión: un préstamo nuevo" in leer(dist, "2025/deuda.html")


@pytest.mark.parametrize("nombre", PAGINAS_ANIO + RAIZ)
def test_cada_pagina_trae_texto_sin_js(dist, nombre):
    assert len(texto_visible(leer(dist, nombre)).split()) >= 100 and "<noscript>" in leer(dist, nombre)


@pytest.mark.parametrize("nombre", [ruta(i, a) for a in ANIOS for i in IDS_ANIO])
def test_relacionado_y_otros_anios_son_del_mismo_anio(dist, nombre):
    anio, _ = nombre.split("/")
    html = leer(dist, nombre)
    bloque = re.search(r'<nav class="relacionado".*?</nav>', html, re.S)
    if bloque:
        for href in re.findall(r'href="([^"]+)"', bloque.group(0)):
            if re.search(r"\d{4}/", href):
                assert f"../{anio}/" in href, f"{nombre}: «Relacionado» enlaza otro año: {href}"
    otros = re.search(r'<p class="muted otros-anios">(.*?)</p>', html, re.S)
    assert otros, f"{nombre}: sin «Otros años»"
    enlaces = re.findall(r'<a href="([^"]+)">([^<]+)</a>', otros.group(1))
    assert [h.split("/")[1] if h != "../" else str(ULTIMO) for h, _ in enlaces] == [str(a) for a in ANIOS if str(a) != anio]
    assert all(len(t.split()) >= 3 and re.search(r"\d{4}", t) for _, t in enlaces)
    for h, _ in enlaces:
        destino = h + "index.html" if h.endswith("/") else h
        assert (dist / nombre).parent.joinpath(destino).resolve().is_file(), h
    if nombre.endswith("gastos.html"):  # la misma página en los otros años
        assert all(h.endswith("/gastos.html") for h, _ in enlaces)


def test_la_portada_de_la_raiz_enlaza_a_cada_anio(dist):
    html = leer(dist, "index.html")
    bloque = re.search(r'<section class="anios".*?</section>', html, re.S).group(0)
    assert "Presupuestos por año" in bloque
    for a in ANIOS:
        assert f"Presupuesto de {a}: en qué se gasta</a>" in bloque
    assert 'href="2025/"' in bloque and 'href="2024/"' in bloque and f'href="{ULTIMO}/gastos.html"' in bloque


def test_las_paginas_sin_anio_no_llevan_otros_anios(dist):
    for i in SIN_ANIO:
        assert "otros-anios" not in leer(dist, f"{i}.html")


# ---------------------------------------------------------------- rutas relativas con profundidad

ATRIBUTOS = re.compile(r'<html lang="es" data-datos="([^"]*)" data-escudo="([^"]*)" data-actualizado="([^"]*)" data-raiz="([^"]*)" data-ultimo="(\d{4})"(?: data-anio="(\d{4})")?>')


@pytest.mark.parametrize("nombre", TODAS)
def test_los_atributos_de_html_llevan_la_profundidad_y_el_anio(dist, nombre):
    m = ATRIBUTOS.search(leer(dist, nombre))
    assert m, nombre
    datos_, escudo, _, raiz, ultimo, anio = m.groups()
    carpeta = json.loads(leer(dist, "build-manifest.json"))["data/"]
    prefijo = "../" if "/" in nombre else ""
    assert raiz == prefijo and ultimo == str(ULTIMO)
    assert anio == (nombre.split("/")[0] if "/" in nombre else None)  # solo las páginas de una carpeta de año fijan el año
    assert datos_ == f"{prefijo}{carpeta}"
    assert re.fullmatch(rf"{re.escape(prefijo)}img/escudo\.[0-9a-f]{{10}}\.png", escudo) and (dist / nombre).parent.joinpath(escudo).resolve().is_file()
    assert (dist / nombre).parent.joinpath(datos_, "index.json").resolve().is_file()


@pytest.mark.parametrize("nombre", TODAS)
def test_todo_lo_que_referencia_una_pagina_existe_tambien_las_precargas(dist, nombre):
    html = leer(dist, nombre)
    base = (dist / nombre).parent
    prefijo = "../" if "/" in nombre else ""
    refs = [r for r in re.findall(r'(?:href|src)="([^"]+)"', html) if not r.startswith(("http", "data:", "#", "mailto:"))]
    assert refs
    for ref in refs:
        destino = re.split(r"[?#]", ref)[0] or "./"
        fichero = base / destino
        assert (fichero / "index.html" if destino.endswith("/") else fichero).resolve().is_file(), f"{nombre}: {ref} no existe"
    cabecera = html[: html.index("<body>")]
    for ref in re.findall(r'<link rel="(?:modulepreload|preload|stylesheet|icon|apple-touch-icon|manifest)"[^>]*href="([^"]+)"', cabecera):
        assert ref.startswith(prefijo) and not ref.startswith(prefijo + "../"), f"{nombre}: {ref} sin la profundidad correcta"
    assert re.search(r'<script type="module" src="' + re.escape(prefijo) + r'js/', html)
    assert re.search(r'<script src="' + re.escape(prefijo) + r'vendor/chart\.umd\.min\.[0-9a-f]{10}\.js"', html) or "chart" not in html


@pytest.mark.parametrize("nombre", PAGINAS_ANIO)
def test_las_precargas_de_datos_son_los_json_del_anio_de_la_pagina(dist, nombre):
    anio = nombre.split("/")[0]
    carpeta = json.loads(leer(dist, "build-manifest.json"))["data/"]
    precargas = re.findall(r'<link rel="preload" href="([^"]+)" as="fetch"', leer(dist, nombre))
    assert f"../{carpeta}index.json" in precargas
    for p in precargas:
        assert re.fullmatch(rf"\.\./{re.escape(carpeta)}(index\.json|{anio}/[a-z]+\.json|guia-terminos\.json)", p), p
        assert (dist / nombre).parent.joinpath(p).resolve().is_file()


def test_los_enlaces_de_un_anio_van_a_su_carpeta_y_los_de_la_raiz_al_ultimo(dist):
    html = leer(dist, "2025/gastos.html")
    for ref in ["../2025/ingresos.html", "../2025/", "../guia.html", "../comparar.html", "../metodologia.html", "../descargas.html"]:
        assert f'href="{ref}"' in html, ref
    assert "?anio=" not in html
    raiz = leer(dist, "gastos.html")
    assert 'href="2026/ingresos.html"' in raiz and 'href="./"' in raiz and "../" not in re.sub(r"<script.*?</script>", "", raiz, flags=re.S)


@pytest.mark.parametrize("nombre", TODAS + ["404.html"])
def test_sin_estilos_en_linea_ni_colores_y_con_la_csp_intacta(dist, nombre):
    html = leer(dist, nombre)
    assert not re.search(r"\sstyle\s*=", html, re.I) and "<style" not in html.lower()
    assert not re.search(r"<script(?![^>]*\bsrc=)(?![^>]*application/ld\+json)[^>]*>", html)
    assert not re.search(r"#[0-9a-fA-F]{6}\b", re.sub(r'<meta name="theme-color"[^>]*>', "", html))
    csp = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)">', html).group(1)
    assert csp == re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)">', (SITE / "index.html").read_text(encoding="utf-8")).group(1)
    assert "'unsafe-inline'" not in csp


# ---------------------------------------------------------------- 404 y sitemap

def test_la_404_enlaza_a_las_paginas_de_cada_anio_con_rutas_desde_la_raiz(dist):
    html = leer(dist, "404.html")
    for ref in ["/", f"/{ULTIMO}/gastos.html", f"/{ULTIMO}/resumen.html", "/comparar.html", "/guia.html", "/descargas.html"]:
        assert f'href="{ref}"' in html, ref
    for ref in re.findall(r'(?:href|src)="([^"]+)"', html):
        assert ref.startswith(("/", "http", "#", "data:")), ref
        if ref.startswith("/") and not ref.endswith("/"):
            assert (dist / ref.lstrip("/")).is_file(), ref


def test_el_sitemap_lista_cada_url_de_anio_las_paginas_sin_anio_y_la_raiz_sin_alias(dist):
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    raiz = ET.fromstring(leer(dist, "sitemap.xml"))
    urls = [e.find("s:loc", ns).text for e in raiz.findall("s:url", ns)]
    esperadas = {DOMINIO} | {url_de(n) for n in PAGINAS_ANIO if canonica_esperada(n) == url_de(n)} | {url_de(f"{i}.html") for i in SIN_ANIO}
    assert sorted(urls) == sorted(esperadas) and len(urls) == len(set(urls)) == 31
    assert DOMINIO + "2025/gastos.html" in urls and DOMINIO + "2024/" in urls and DOMINIO + "2024/deuda.html" in urls
    for alias in ALIAS:  # los alias de la raíz y la carpeta del último año apuntan a otra canónica: fuera
        assert DOMINIO + alias not in urls
    assert DOMINIO + f"{ULTIMO}/" not in urls
    for e in raiz.findall("s:url", ns):
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", e.find("s:lastmod", ns).text)
    assert all(u.startswith(DOMINIO) for u in urls)


def test_el_lastmod_de_un_anio_sale_de_git_o_de_la_fecha_del_build(tmp_path):
    destino = tmp_path / "dist"
    os.environ["SOURCE_DATE_EPOCH"] = "1700000000"
    try:
        copia = tmp_path / "site"
        import shutil
        shutil.copytree(SITE, copia)  # sin historial git: cae a SOURCE_DATE_EPOCH, así es reproducible
        build_site.build(copia, destino)
    finally:
        del os.environ["SOURCE_DATE_EPOCH"]
    assert "<lastmod>2023-11-14</lastmod>" in leer(destino, "sitemap.xml")


def test_el_manifiesto_incluye_las_paginas_de_cada_anio(dist):
    m = json.loads(leer(dist, "build-manifest.json"))
    for n in PAGINAS_ANIO:
        assert m[n] == n
