"""Datos estructurados (JSON-LD) y precarga de módulos y datos en el HTML generado."""
import json
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
DOMINIO = "https://presupuestos.arandadeduero.dev/"
sys.path.insert(0, str(ROOT / "tools"))
import build_site  # noqa: E402

PAGINAS = sorted(p.name for p in SITE.glob("*.html"))
SIN_ANIO = ["comparar.html", "guia.html", "metodologia.html", "descargas.html"]
ULTIMO = json.loads((SITE / "data" / "index.json").read_text(encoding="utf-8"))["ultimo"]
BLOQUE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    if os.environ.get("DIST_DIR"):
        return Path(os.environ["DIST_DIR"])
    destino = tmp_path_factory.mktemp("dist_ld")
    build_site.build(SITE, destino)
    return destino


def nodos(dist, pagina):
    html = (dist / pagina).read_text(encoding="utf-8")
    salida = []
    for b in BLOQUE.findall(html):
        datos = json.loads(b)  # JSON válido
        assert datos["@context"] == "https://schema.org"
        salida += datos.get("@graph", [datos])
    return salida


def tipos(nodos_):
    return [n["@type"] for n in nodos_]


def urls(valor):
    """Todas las cadenas que son URL dentro de un valor JSON."""
    if isinstance(valor, str):
        if valor.startswith(("http", "/")):
            yield valor
    elif isinstance(valor, dict):
        for k, v in valor.items():
            if k in ("url", "item", "contentUrl", "logo", "@id", "sameAs", "image"):
                yield from urls(v)
            elif isinstance(v, (dict, list)):
                yield from urls(v)
    elif isinstance(valor, list):
        for v in valor:
            yield from urls(v)


@pytest.mark.parametrize("pagina", PAGINAS)
def test_todas_las_urls_de_los_datos_estructurados_son_absolutas(dist, pagina):
    for n in nodos(dist, pagina):
        for u in urls(n):
            assert u.startswith("https://"), f"{pagina}: {u}"


def test_la_portada_tiene_website_y_organizacion_enlazados(dist):
    ns = {n["@type"]: n for n in nodos(dist, "index.html")}
    assert set(ns) == {"WebSite", "GovernmentOrganization"}
    org, web = ns["GovernmentOrganization"], ns["WebSite"]
    assert web["publisher"] == {"@id": org["@id"]}
    assert org["url"] == "https://www.arandadeduero.es" and org["sameAs"] == ["https://github.com/arandadeduero"]
    manifiesto = json.loads((dist / "build-manifest.json").read_text(encoding="utf-8"))
    assert org["logo"] == DOMINIO + manifiesto["img/escudo.png"]
    assert (dist / org["logo"].removeprefix(DOMINIO)).is_file()
    assert "potentialAction" not in web  # sin SearchAction


@pytest.mark.parametrize("pagina", [p for p in PAGINAS if p != "index.html"])
def test_las_paginas_interiores_tienen_migas_de_pan(dist, pagina):
    migas = [n for n in nodos(dist, pagina) if n["@type"] == "BreadcrumbList"]
    assert len(migas) == 1
    items = migas[0]["itemListElement"]
    if pagina in SIN_ANIO:
        assert [i["position"] for i in items] == [1, 2]
        assert items[0]["item"] == DOMINIO and items[1]["item"] == DOMINIO + pagina
    else:  # alias del último año: las migas son las de su página en /<último año>/ (ver test_anios.py)
        assert [i["position"] for i in items] == [1, 2, 3]
        assert items[0]["item"] == DOMINIO and items[2]["item"] == DOMINIO + f"{ULTIMO}/{pagina}"


def test_descargas_tiene_un_dataset_por_anio_con_distribuciones_que_existen(dist):
    datasets = [n for n in nodos(dist, "descargas.html") if n["@type"] == "Dataset"]
    indice = json.loads((SITE / "data" / "index.json").read_text(encoding="utf-8"))
    assert [d["temporalCoverage"] for d in datasets] == [str(a["anio"]) for a in indice["anios"]]
    for d in datasets:
        for clave in ["name", "description", "inLanguage", "isAccessibleForFree", "creator", "temporalCoverage", "spatialCoverage", "distribution"]:
            assert d.get(clave) not in (None, ""), clave
        assert d["inLanguage"] == "es" and d["isAccessibleForFree"] is True
        assert "Aranda de Duero" in d["spatialCoverage"]["name"] and "Burgos" in d["spatialCoverage"]["name"]
        assert "license" not in d  # pendiente: el usuario aún no ha decidido la licencia de los datos
        json_ = [x for x in d["distribution"] if x["encodingFormat"] == "application/json"]
        assert len(json_) == 6
        for x in json_:
            assert x["@type"] == "DataDownload"
            assert (dist / x["contentUrl"].removeprefix(DOMINIO)).is_file(), x["contentUrl"]
        excels = [x for x in d["distribution"] if x["encodingFormat"].endswith("spreadsheetml.sheet")]
        assert excels, "faltan los Excel originales"
        for x in excels:
            assert x["contentUrl"].startswith(f"https://github.com/arandadeduero/visorpresupuesto/raw/main/{d['temporalCoverage']}/")
            assert x["contentUrl"].endswith(".xlsx")


def test_calculadora_es_una_aplicacion_web_gratuita(dist):
    app = next(n for n in nodos(dist, "calculadora.html") if n["@type"] == "WebApplication")
    assert app["isAccessibleForFree"] is True and app["offers"]["price"] == "0" and app["url"] == DOMINIO + f"{ULTIMO}/calculadora.html"


def test_la_guia_tiene_un_defined_term_por_termino(dist):
    conjunto = next(n for n in nodos(dist, "guia.html") if n["@type"] == "DefinedTermSet")
    terminos = json.loads((SITE / "data" / "guia-terminos.json").read_text(encoding="utf-8"))
    assert [t["name"] for t in conjunto["hasDefinedTerm"]] == [t["termino"] for t in terminos]
    assert all(t["@type"] == "DefinedTerm" and t["description"] and t["url"].startswith(DOMINIO + "guia.html#") for t in conjunto["hasDefinedTerm"])


def test_no_se_usan_tipos_no_respaldados_por_el_contenido(dist):
    for p in PAGINAS:
        assert not {"FAQPage", "SearchAction"} & set(json.dumps(nodos(dist, p)).replace('"', " ").split())


def test_la_404_no_lleva_datos_estructurados_ni_precargas(dist):
    html = (dist / "404.html").read_text(encoding="utf-8")
    assert "ld+json" not in html and "modulepreload" not in html and 'as="fetch"' not in html


# ---------------------------------------------------------------- rendimiento

@pytest.mark.parametrize("pagina", PAGINAS)
def test_modulepreload_y_preload_apuntan_a_ficheros_que_existen(dist, pagina):
    html = (dist / pagina).read_text(encoding="utf-8")
    modulos = re.findall(r'<link rel="modulepreload" href="([^"]+)">', html)
    assert modulos and all((dist / m).is_file() for m in modulos)
    principal = re.search(r'<script type="module" src="([^"]+)"', html).group(1)
    assert modulos[0] == principal
    assert html.index('rel="modulepreload"') < html.index('<script type="module"')
    cargas = re.findall(r'<link rel="preload" href="([^"]+)" as="fetch" crossorigin>', html)
    carpeta = json.loads((dist / "build-manifest.json").read_text(encoding="utf-8"))["data/"]
    assert cargas[0] == f"{carpeta}index.json" and all((dist / c).is_file() for c in cargas)


def test_cada_pagina_precarga_los_json_que_usa(dist):
    esperado = {
        "index.html": ["resumen"], "deuda.html": ["deuda", "inversiones"], "indicadores.html": ["resumen", "ingresos", "deuda"],
        "gastos.html": ["gastos", "resumen"], "calculadora.html": ["gastos"], "inversiones.html": ["inversiones"],
    }
    ultimo = json.loads((SITE / "data" / "index.json").read_text(encoding="utf-8"))["ultimo"]
    for pagina, nombres in esperado.items():
        html = (dist / pagina).read_text(encoding="utf-8")
        cargas = re.findall(r'<link rel="preload" href="[^"]*/(\d{4})/([a-z]+)\.json"', html)
        assert sorted(n for _, n in cargas) == sorted(nombres), pagina
        assert {a for a, _ in cargas} == {str(ultimo)}
    assert "gastos.json" not in (dist / "index.html").read_text(encoding="utf-8").split("</head>")[0]  # la portada no precarga lo diferido
    assert "guia-terminos.json" in (dist / "guia.html").read_text(encoding="utf-8").split("</head>")[0]


def test_chart_js_solo_en_las_paginas_con_graficos_y_con_defer_antes_del_modulo(dist):
    con_graficos = {"comparar.html", "deuda.html", "gastos.html", "ingresos.html", "resumen.html"}
    for pagina in PAGINAS:
        html = (dist / pagina).read_text(encoding="utf-8")
        tiene = "vendor/chart.umd.min." in html
        assert tiene == (pagina in con_graficos), pagina
        if tiene:
            m = re.search(r'<script src="(vendor/chart[^"]+)" defer></script>', html)
            assert m and html.index(m.group(0)) < html.index('<script type="module"')


def test_el_resto_de_paginas_cargan_solo_los_json_que_pintan(dist):
    # Ninguna página (salvo comparar y la portada diferida) pide un JSON que no use
    for js in SITE.glob("js/*.js"):
        if js.name.endswith(".test.js"):
            continue
        fuente = js.read_text(encoding="utf-8")
        for nombre in re.findall(r'\bload\("([a-z]+)"\)', fuente):
            usos = len(re.findall(r"\b" + {"resumen": r"(?:resumen|\br\b)", "gastos": r"(?:gastos|datos)", "ingresos": r"(?:ingresos|datos)", "deuda": r"(?:\bd\b|deuda)", "inversiones": r"(?:inv|\bd\b)", "subvenciones": r"\bd\b"}[nombre], fuente))
            assert usos >= 2, f"{js.name} carga {nombre} y no lo usa"
