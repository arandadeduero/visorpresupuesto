"""Cabecera extra de cada HTML de dist/: datos estructurados (JSON-LD) y precarga de módulos y datos.

Todo se genera en el build con los nombres con huella del manifiesto y los JSON de site/data; nada se escribe a mano.
"""
import json
import re
from pathlib import Path

import prerender

DOMINIO = "https://presupuestos.arandadeduero.dev/"
URL_AYUNTAMIENTO = "https://www.arandadeduero.es"
ID_ORGANIZACION = DOMINIO + "#ayuntamiento"
ID_WEB = DOMINIO + "#web"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
IMPORT = re.compile(r'(?:\bfrom|\bimport)\s*"\./([^"]+\.js)"')
# Datos que una página pide pero no hacen falta para pintar lo primero (no se precargan)
SIN_PRECARGA = {"inicio": {"gastos"}}


def url_pagina(href: str) -> str:
    return DOMINIO if href == "index.html" else DOMINIO + href


def organizacion() -> dict:
    return {
        "@type": "GovernmentOrganization",
        "@id": ID_ORGANIZACION,
        "name": "Ayuntamiento de Aranda de Duero",
        "url": URL_AYUNTAMIENTO,
        "sameAs": ["https://github.com/arandadeduero"],
    }


def dataset(ctx, anio: int, manifiesto: dict) -> dict:
    """Un conjunto de datos por año: los JSON de la web (con huella) y los Excel originales. Sin licencia: pendiente de decidir."""
    distribucion = [
        {
            "@type": "DataDownload",
            "name": f"{prerender.NOMBRE_JSON[f][0]} {anio} (JSON)",
            "encodingFormat": "application/json",
            "contentUrl": DOMINIO + ctx.url_json(anio, f),
        }
        for f in prerender.ORDEN_JSON
    ] + [
        {"@type": "DataDownload", "name": n, "encodingFormat": XLSX, "contentUrl": prerender.url_excel(anio, n)}
        for n in ctx.excels.get(anio, [])
    ]
    return {
        "@type": "Dataset",
        "@id": f"{DOMINIO}descargas.html#presupuesto-{anio}",
        "name": f"Presupuesto inicial {anio} del Ayuntamiento de Aranda de Duero",
        "description": f"Ingresos, gastos, inversiones, subvenciones y deuda del presupuesto inicial {anio} del Ayuntamiento de Aranda de Duero, en JSON y en los Excel originales del Ayuntamiento.",
        "url": DOMINIO + "descargas.html",
        "inLanguage": "es",
        "isAccessibleForFree": True,
        "creator": {"@id": ID_ORGANIZACION},
        "temporalCoverage": str(anio),
        "spatialCoverage": {"@type": "Place", "name": "Aranda de Duero, Burgos, España"},
        "distribution": distribucion,
    }


def nodos(pagina: str, href: str, titulo: str, ctx, manifiesto: dict) -> list:
    """Nodos JSON-LD de una página."""
    salida = []
    if pagina == "inicio":
        salida.append({"@type": "WebSite", "@id": ID_WEB, "url": DOMINIO, "name": "Presupuestos de Aranda de Duero", "inLanguage": "es", "publisher": {"@id": ID_ORGANIZACION}})
        org = organizacion()
        org["logo"] = DOMINIO + ctx.escudo
        salida.append(org)
    else:
        salida.append({
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Inicio", "item": DOMINIO},
                {"@type": "ListItem", "position": 2, "name": titulo, "item": url_pagina(href)},
            ],
        })
    if pagina == "descargas":
        salida.append(organizacion())
        salida += [dataset(ctx, a, manifiesto) for a in sorted(ctx.anios)]
    elif pagina == "calculadora":
        salida.append({
            "@type": "WebApplication",
            "name": "Calculadora: ¿a qué se destinan mis impuestos?",
            "url": url_pagina(href),
            "description": "Reparte de forma orientativa lo que pagas de IBI, impuesto de vehículos y tasas entre los gastos previstos del Ayuntamiento de Aranda de Duero.",
            "applicationCategory": "FinanceApplication",
            "operatingSystem": "Web",
            "inLanguage": "es",
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
        })
    elif pagina == "guia":
        salida.append({
            "@type": "DefinedTermSet",
            "@id": url_pagina(href) + "#glosario",
            "name": "Glosario del presupuesto municipal",
            "url": url_pagina(href),
            "inLanguage": "es",
            "hasDefinedTerm": [
                {"@type": "DefinedTerm", "name": t["termino"], "description": t["definicion"], "url": f"{url_pagina(href)}#{prerender.id_termino(t['termino'])}"}
                for t in ctx.terminos
            ],
        })
    return salida


def bloque_jsonld(lista: list) -> str:
    grafo = {"@context": "https://schema.org", "@graph": lista}
    texto = json.dumps(grafo, ensure_ascii=False, indent=2).replace("<", "\\u003c")  # nunca cierra el <script> antes de tiempo
    return f'  <script type="application/ld+json">\n{texto}\n  </script>\n'


# ---------------------------------------------------------------- precarga

def cadena_de_modulos(dist: Path, modulo: str) -> list:
    """El módulo y todos los que importa (con huella, recursivo), en orden de descubrimiento."""
    vistos, cola = [], [modulo]
    while cola:
        actual = cola.pop(0)
        if actual in vistos:
            continue
        vistos.append(actual)
        cola += IMPORT.findall((dist / "js" / actual).read_text(encoding="utf-8"))
    return vistos


def datos_de_la_pagina(site: Path, pagina: str, modulo_fuente: str) -> list:
    """JSON de datos que pide el módulo de la página (se lee de su código: load("x") y getGuiaTerminos)."""
    fuente = (site / "js" / modulo_fuente).read_text(encoding="utf-8")
    nombres = [n for n in dict.fromkeys(re.findall(r'\bload\("([a-z]+)"\)', fuente)) if n not in SIN_PRECARGA.get(pagina, set())]
    return nombres


def precarga(site: Path, dist: Path, ctx, manifiesto: dict, pagina: str, html: str) -> str:
    """<link> de modulepreload (módulo de la página y sus imports) y preload de index.json y de los datos de la página."""
    m = re.search(r'<script type="module" src="js/([^"]+)"', html)
    if not m:
        return ""
    modulo = m.group(1)
    original = next(k for k, v in manifiesto.items() if v == f"js/{modulo}")  # js/home.js
    enlaces = [f'  <link rel="modulepreload" href="js/{n}">\n' for n in cadena_de_modulos(dist, modulo)]
    datos = [f"{ctx.carpeta_datos}index.json"]
    datos += [ctx.url_json(ctx.ultimo, n) for n in datos_de_la_pagina(site, pagina, Path(original).name)]
    if "getGuiaTerminos" in (site / original).read_text(encoding="utf-8"):
        datos.append(f"{ctx.carpeta_datos}guia-terminos.json")
    enlaces += [f'  <link rel="preload" href="{d}" as="fetch" crossorigin>\n' for d in datos]
    return "".join(enlaces)
