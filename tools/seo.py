"""Cabecera de cada HTML de dist/: título, descripción y URL canónica de cada año, datos estructurados (JSON-LD) y precarga de módulos y datos.

Todo se genera en el build con los nombres con huella del manifiesto y los JSON de site/data; los años salen de site/data/index.json.
"""
import html
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


# ---------------------------------------------------------------- páginas de cada año

# Páginas que dependen del año: viven en /<año>/ (y la raíz guarda un alias del último año). El resto (comparar, guía,
# metodología, descargas) no tienen año.
PAGINAS_ANIO = ["inicio", "resumen", "ingresos", "gastos", "inversiones", "subvenciones", "deuda", "indicadores", "calculadora"]

# Título (hasta 60 caracteres) y descripción (120-160) de cada página en un año. Llevan el año y ninguna cifra.
TEXTOS_ANIO = {
    "inicio": ("Presupuesto de Aranda de Duero {a}: en qué se gasta",
               "Mira por cada 100 € en qué prevé gastar el Ayuntamiento de Aranda de Duero en {a}: personal, servicios, obras y deuda. Datos del presupuesto inicial."),
    "resumen": ("Resumen del presupuesto de Aranda de Duero en {a}",
                "Resumen del presupuesto de {a} del Ayuntamiento de Aranda de Duero: cuánto prevé ingresar y gastar, por capítulos, y qué ha cambiado respecto al año anterior."),
    "ingresos": ("Ingresos del Ayuntamiento de Aranda de Duero en {a}",
                 "De dónde sale el dinero del Ayuntamiento de Aranda de Duero en {a}: impuestos, tasas, transferencias y préstamos, por capítulos y conceptos."),
    "gastos": ("Gastos del Ayuntamiento de Aranda de Duero en {a}",
               "En qué gasta el Ayuntamiento de Aranda de Duero en {a}: cultura, seguridad, limpieza, personal y más. Gastos por política, por capítulo y hasta cada partida."),
    "inversiones": ("Inversiones y obras previstas en Aranda de Duero en {a}",
                    "Obras y compras que prevé el Ayuntamiento de Aranda de Duero en {a}: cuánto se invierte, en qué proyectos y cómo se pagan (préstamo, ahorros o subvenciones)."),
    "subvenciones": ("Subvenciones del Ayuntamiento de Aranda de Duero en {a}",
                     "A qué asociaciones y entidades da dinero el Ayuntamiento de Aranda de Duero en {a}: subvenciones nominativas y cuotas, por actividad y por entidad."),
    "deuda": ("Deuda del Ayuntamiento de Aranda de Duero en {a}",
              "Cuánto debe el Ayuntamiento de Aranda de Duero en {a}: préstamos vivos, evolución de la deuda, coste anual en intereses y amortización, y el préstamo previsto."),
    "indicadores": ("Indicadores financieros de Aranda de Duero en {a}",
                    "Indicadores financieros de Aranda de Duero en {a}: ahorro bruto, deuda por habitante, nivel de endeudamiento y dependencia de otras administraciones."),
    "calculadora": ("¿A qué se destinan mis impuestos? Calculadora {a}",
                    "Calcula a qué se destina lo que pagas de IBI, impuesto de vehículos y tasas en Aranda de Duero según el gasto previsto en {a}: un reparto orientativo."),
}


def textos_anio(pagina: str, anio: int) -> tuple:
    titulo, descripcion = TEXTOS_ANIO[pagina]
    return titulo.format(a=anio), descripcion.format(a=anio)


def ruta_anio(pagina: str, anio: int) -> str:
    """Ruta de una página en la carpeta de su año: 2025/gastos.html (la portada del año es 2025/)."""
    return f"{anio}/" if pagina == "inicio" else f"{anio}/{pagina}.html"


def poner_cabecera(cabecera: str, titulo: str | None = None, descripcion: str | None = None, canonical: str | None = None) -> str:
    """Cambia título, descripción y URL canónica de un HTML (y sus copias en Open Graph y Twitter) por los de esta página."""
    def sustituye(patron, valor, texto):
        nuevo, n = re.subn(patron, lambda m: m.group(1) + valor + m.group(2), texto, count=1, flags=re.S)
        if n != 1:
            raise ValueError(f"Falta {patron} en el HTML")
        return nuevo

    if titulo is not None:
        t = html.escape(titulo, quote=True)
        cabecera = sustituye(r"(<title>)[^<]*(</title>)", t, cabecera)
        cabecera = sustituye(r'(<meta property="og:title" content=")[^"]*(">)', t, cabecera)
        cabecera = sustituye(r'(<meta name="twitter:title" content=")[^"]*(">)', t, cabecera)
    if descripcion is not None:
        d = html.escape(descripcion, quote=True)
        cabecera = sustituye(r'(<meta name="description" content=")[^"]*(">)', d, cabecera)
        cabecera = sustituye(r'(<meta property="og:description" content=")[^"]*(">)', d, cabecera)
        cabecera = sustituye(r'(<meta name="twitter:description" content=")[^"]*(">)', d, cabecera)
    if canonical is not None:
        cabecera = sustituye(r'(<link rel="canonical" href=")[^"]*(">)', canonical, cabecera)
        cabecera = sustituye(r'(<meta property="og:url" content=")[^"]*(">)', canonical, cabecera)
    return cabecera


def organizacion() -> dict:
    return {
        "@type": "GovernmentOrganization",
        "@id": ID_ORGANIZACION,
        "name": "Ayuntamiento de Aranda de Duero",
        "url": URL_AYUNTAMIENTO,
        "sameAs": ["https://github.com/arandadeduero"],
    }


def dataset(ctx, anio: int) -> dict:
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


def nodos(pagina: str, texto: str, url: str, ctx, anio: int | None = None) -> list:
    """Nodos JSON-LD de una página. `url` es su URL canónica; `anio`, el año de las páginas que dependen de él (migas Inicio › 2025 › Gastos)."""
    salida = []
    if pagina == "inicio" and anio is None:
        salida.append({"@type": "WebSite", "@id": ID_WEB, "url": DOMINIO, "name": "Presupuestos de Aranda de Duero", "inLanguage": "es", "publisher": {"@id": ID_ORGANIZACION}})
        org = organizacion()
        org["logo"] = DOMINIO + ctx.escudo
        salida.append(org)
    else:
        migas = [("Inicio", DOMINIO)]
        if anio is not None:
            migas.append((f"Presupuesto {anio}", f"{DOMINIO}{anio}/"))
        if pagina != "inicio":
            migas.append((texto, url))
        salida.append({
            "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i, "name": n, "item": u} for i, (n, u) in enumerate(migas, 1)],
        })
    if pagina == "descargas":
        salida.append(organizacion())
        salida += [dataset(ctx, a) for a in sorted(ctx.anios)]
    elif pagina == "calculadora":
        salida.append({
            "@type": "WebApplication",
            "name": "Calculadora: ¿a qué se destinan mis impuestos?",
            "url": url,
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
            "@id": url + "#glosario",
            "name": "Glosario del presupuesto municipal",
            "url": url,
            "inLanguage": "es",
            "hasDefinedTerm": [
                {"@type": "DefinedTerm", "name": t["termino"], "description": t["definicion"], "url": f"{url}#{prerender.id_termino(t['termino'])}"}
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


def precarga(site: Path, dist: Path, ctx, manifiesto: dict, pagina: str, html: str, prefijo: str = "") -> str:
    """<link> de modulepreload (módulo de la página y sus imports) y preload de index.json y de los datos del año de la página.
    `prefijo` es la ruta de vuelta a la raíz desde la carpeta de la página («../» en /2025/)."""
    m = re.search(r'<script type="module" src="(?:\.\./)?js/([^"]+)"', html)
    if not m:
        return ""
    modulo = m.group(1)
    original = next(k for k, v in manifiesto.items() if v == f"js/{modulo}")  # js/home.js
    enlaces = [f'  <link rel="modulepreload" href="{prefijo}js/{n}">\n' for n in cadena_de_modulos(dist, modulo)]
    datos = [f"{ctx.carpeta_datos}index.json"]
    datos += [ctx.url_json(ctx.anio, n) for n in datos_de_la_pagina(site, pagina, Path(original).name)]
    if "getGuiaTerminos" in (site / original).read_text(encoding="utf-8"):
        datos.append(f"{ctx.carpeta_datos}guia-terminos.json")
    enlaces += [f'  <link rel="preload" href="{prefijo}{d}" as="fetch" crossorigin>\n' for d in datos]
    return "".join(enlaces)
