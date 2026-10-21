#!/usr/bin/env python3
"""Construye dist/ a partir de site/ poniendo una huella (hash del contenido) en el nombre de los ficheros estáticos.

Uso: python3 tools/build_site.py [site] [dist]

- css (styles.css, escalas.css), js (módulos incluidos), vendor y tipografías (woff2) se renombran: styles.<huella>.css, home.<huella>.js...
- Los módulos se procesan en orden topológico: su huella sale de su contenido ya con los imports reescritos,
  así un cambio en format.js cambia también la huella de todos los que lo importan (y la de los HTML).
- data/ se copia a data-<huella>/ (huella de todo el directorio) y cada HTML recibe data-datos="data-<huella>/".
- img/: social.png y los iconos conservan su nombre (URL estable); el resto (escudo.png de la cabecera) lleva huella y su ruta
  se anota en cada HTML como data-escudo="img/escudo.<huella>.png" (lo lee layout.js).
- manifest.webmanifest y robots.txt se copian tal cual.
- Cada año publicado (site/data/index.json) tiene su carpeta con las páginas que dependen del año: /2025/ (portada), /2025/gastos.html...
  Salen de los mismos site/*.html, un nivel por debajo de la raíz: las rutas relativas se reescriben (../css/..., data-datos="../data-<huella>/")
  y <html> lleva data-raiz="../", data-anio="2025" y data-ultimo="2026" (los lee site/js/rutas.js). Las páginas de la raíz son el último año
  (la portada y los alias /gastos.html... con canonical a /2026/gastos.html) y las que no dependen del año (comparar, guía, metodología, descargas).
- Los HTML y los enlaces entre páginas conservan su nombre. Cada HTML sale con el contenido estático (tools/prerender.py) en
  lugar de «Cargando…», para quien no ejecuta JavaScript; el navegador lo sustituye al pintar la página. Título, descripción,
  URL canónica y datos estructurados son los de cada año (tools/seo.py).
- sitemap.xml se genera con <lastmod> (fecha del último commit que toca los datos del año o el código de site/) y solo lista las
  páginas cuya canónica es ella misma. 404.html (con noindex) se construye aquí.
- dist/build-manifest.json relaciona cada original con su fichero publicado.
"""
import hashlib
import json
import re
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prerender  # noqa: E402
import seo  # noqa: E402

LARGO = 10
IMPORT = re.compile(r'((?:\bfrom|\bimport)\s*)"(\./[^"]+\.js)"')
REF_HTML = re.compile(r'((?:href|src)=")([^"#:]+\.(?:css|js|woff2))(")')
URL_FUENTE = re.compile(r"url\(\.\./(fonts/[^)]+\.woff2)\)")
# Con URL estable (sin huella): la imagen para compartir y los iconos los piden por nombre los rastreadores y los navegadores
IMG_ESTABLES = {"social.png", "favicon-32.png", "apple-touch-icon.png", "icon-192.png", "icon-512.png"}
FICHEROS_RAIZ = ["manifest.webmanifest", "robots.txt"]
DOMINIO = "https://presupuestos.arandadeduero.dev/"
CARGANDO = '<p class="cargando wrap">Cargando…</p>'
REF_RELATIVA = re.compile(r'((?:href|src)=")(?!https?:|data:|#|/)([^"]*")')
PLANTILLA = re.compile(r'\s*<template id="contenido-estatico">(.*?)</template>\n?', re.S)
RAIZ = Path(__file__).resolve().parents[1]


class CicloDeImportaciones(Exception):
    pass


def huella(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()[:LARGO]


def con_huella(ruta: str, h: str) -> str:
    base, punto, ext = ruta.rpartition(".")
    return f"{base}.{h}.{ext}"


def huella_directorio(directorio: Path) -> str:
    resumen = hashlib.sha256()
    for f in sorted(p for p in directorio.rglob("*") if p.is_file()):
        resumen.update(f.relative_to(directorio).as_posix().encode())
        resumen.update(b"\0" + hashlib.sha256(f.read_bytes()).digest())
    return resumen.hexdigest()[:LARGO]


def _modulos(site: Path) -> dict[str, Path]:
    return {f"js/{p.name}": p for p in sorted((site / "js").glob("*.js")) if not p.name.endswith(".test.js")}


def _publicar_modulos(site: Path, dist: Path, manifiesto: dict) -> None:
    fuentes = {rel: p.read_text(encoding="utf-8") for rel, p in _modulos(site).items()}
    estado: dict[str, str] = {}  # rel -> "visitando" | "hecho"

    def destino(rel, spec):
        return "js/" + spec[2:]

    def visita(rel, camino):
        if estado.get(rel) == "hecho":
            return
        if estado.get(rel) == "visitando":
            ciclo = camino[camino.index(rel):] + [rel]
            raise CicloDeImportaciones("Ciclo de importaciones: " + " -> ".join(ciclo))
        estado[rel] = "visitando"
        for _, spec in IMPORT.findall(fuentes[rel]):
            dep = destino(rel, spec)
            if dep not in fuentes:
                raise FileNotFoundError(f"{rel} importa {spec}, que no existe en {site}")
            visita(dep, camino + [rel])

        def cambia(m):
            return f'{m.group(1)}"./{Path(manifiesto[destino(rel, m.group(2))]).name}"'

        texto = IMPORT.sub(cambia, fuentes[rel])
        nombre = con_huella(rel, huella(texto.encode()))
        manifiesto[rel] = nombre
        (dist / nombre).write_text(texto, encoding="utf-8")
        estado[rel] = "hecho"

    for rel in fuentes:
        visita(rel, [])


def _publicar_estaticos(site: Path, dist: Path, manifiesto: dict) -> None:
    # Tipografías primero: el css las referencia y su huella depende de las de las fuentes
    for p in sorted((site / "fonts").glob("*.woff2")):
        rel = f"fonts/{p.name}"
        datos = p.read_bytes()
        nombre = con_huella(rel, huella(datos))
        manifiesto[rel] = nombre
        (dist / nombre).write_bytes(datos)
    for p in (site / "fonts").glob("*"):
        if p.suffix != ".woff2":  # licencia y README, tal cual
            shutil.copy2(p, dist / "fonts" / p.name)

    for ruta in sorted((site / "css").glob("*.css")):
        rel = f"css/{ruta.name}"
        css = ruta.read_text(encoding="utf-8")

        def url(m, rel=rel):
            if m.group(1) not in manifiesto:
                raise FileNotFoundError(f"{rel} usa {m.group(1)}, que no existe en {site}")
            return f"url(../{manifiesto[m.group(1)]})"

        css = URL_FUENTE.sub(url, css)
        nombre = con_huella(rel, huella(css.encode()))
        manifiesto[rel] = nombre
        (dist / nombre).write_text(css, encoding="utf-8")

    for p in sorted((site / "img").glob("*.png")):
        rel = f"img/{p.name}"
        datos = p.read_bytes()
        nombre = rel if p.name in IMG_ESTABLES else con_huella(rel, huella(datos))
        manifiesto[rel] = nombre
        (dist / nombre).write_bytes(datos)
    shutil.copy2(site / "img" / "README.md", dist / "img" / "README.md")
    for f in FICHEROS_RAIZ:
        shutil.copy2(site / f, dist / f)

    for rel in sorted(f"vendor/{p.name}" for p in (site / "vendor").glob("*.js")):
        datos = (site / rel).read_bytes()
        nombre = con_huella(rel, huella(datos))
        manifiesto[rel] = nombre
        (dist / nombre).write_bytes(datos)


def fecha_de_git(site: Path, ruta) -> str:
    """Fecha (AAAA-MM-DD) del último commit que toca `ruta` (o la lista de rutas; relativas a la carpeta que contiene site/).
    Determinista en CI (el checkout debe traer el historial). Sin git o sin historial: SOURCE_DATE_EPOCH o el día de hoy."""
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%cs", "--", *([ruta] if isinstance(ruta, str) else ruta)], cwd=Path(site).resolve().parent, capture_output=True, text=True)
        if r.returncode == 0 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", r.stdout.strip()):
            return r.stdout.strip()
    except OSError:
        pass
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    ahora = datetime.fromtimestamp(int(epoch), timezone.utc) if epoch else datetime.now(timezone.utc)
    return ahora.strftime("%Y-%m-%d")


def excels_por_anio(site: Path, anios: list) -> dict:
    """Nombres de los Excel originales de cada año (carpeta <año>/ junto a site/), para enlazarlos desde Descargas."""
    salida = {}
    for a in anios:
        carpeta = Path(site).resolve().parent / str(a)
        salida[a] = sorted(p.name for p in carpeta.glob("*.xlsx")) if carpeta.is_dir() else []
    return salida


def sitemap(paginas: list) -> str:
    """paginas: [(URL absoluta, lastmod)]. Solo van las páginas cuya canónica es ella misma (los alias no)."""
    urls = "".join(f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod></url>\n" for url, lastmod in paginas)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n'


def desde_la_raiz(fragmento: str) -> str:
    """Rutas relativas -> rutas desde la raíz del dominio (la 404 se sirve en cualquier URL, también en subcarpetas)."""
    def cambia(m):
        ruta = m.group(2)
        return f'{m.group(1)}="/{"" if ruta in ("./", "index.html") else ruta}"'

    return re.sub(r'(href|src)="(?!https?:|data:|#|/)([^"]*)"', cambia, fragmento)


def pagina_404(base_html: str, ctx) -> str:
    """404.html: sin canonical ni JS, con noindex, con el menú y la lista de páginas como enlaces normales."""
    cabecera = base_html[: base_html.index("<body>")]
    cabecera = re.sub(r'\s*<link rel="(?:modulepreload|preload)" href="(?:js/|data-)[^>]*>|\s*<script type="application/ld\+json">.*?</script>', "", cabecera, flags=re.S)
    cabecera = re.sub(r"\s*<link rel=\"canonical\"[^>]*>", "", cabecera)
    cabecera = re.sub(r"\s*<meta (?:property=\"og:|name=\"twitter:)[^>]*>", "", cabecera)
    cabecera = re.sub(r"<title>.*?</title>", "<title>Página no encontrada · Presupuestos de Aranda de Duero</title>", cabecera, flags=re.S)
    cabecera = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="La página que buscas no existe. Mira los presupuestos del Ayuntamiento de Aranda de Duero desde la portada o el menú.">', cabecera)
    cabecera = cabecera.replace('<meta name="color-scheme"', '<meta name="robots" content="noindex">\n  <meta name="color-scheme"', 1)
    urls = ctx.e["urls"]
    enlaces = "".join(f'<li><a href="{urls[id_]}">{prerender.esc(t)}</a></li>' for id_, t, _ in ctx.js["secciones"])
    contenido = (
        "<h1>Página no encontrada</h1>"
        '<p class="lead">La dirección que has escrito no existe o ha cambiado. Estas son las páginas de la web:</p>'
        f'<ul class="descargas">{enlaces}</ul>'
    )
    marco = ctx.e["marcos"]["inicio"].replace(ctx.js["marca"], contenido).replace(' aria-current="page"', "")
    return desde_la_raiz(cabecera) + "<body>" + desde_la_raiz(marco) + "\n</body>\n</html>\n"


def build(site: Path, dist: Path) -> dict:
    site, dist = Path(site), Path(dist)
    if dist.exists():
        shutil.rmtree(dist)
    for sub in ["css", "js", "vendor", "fonts", "img"]:
        (dist / sub).mkdir(parents=True)
    manifiesto: dict[str, str] = {}

    _publicar_estaticos(site, dist, manifiesto)
    _publicar_modulos(site, dist, manifiesto)

    carpeta_datos = f"data-{huella_directorio(site / 'data')}/"
    shutil.copytree(site / "data", dist / carpeta_datos)
    manifiesto["data/"] = carpeta_datos

    # Ficheros que se sirven tal cual (licencias, README de vendor) por si alguien los enlaza
    for p in (site / "vendor").glob("*.md"):
        shutil.copy2(p, dist / "vendor" / p.name)

    escudo = manifiesto["img/escudo.png"]
    lastmod = fecha_de_git(site, site.name)
    codigo = fecha_de_git(site, [site.name, f":(exclude){site.name}/data"])  # lo que no son datos: HTML, JS, CSS
    actualizado = fecha_de_git(site, f"{site.name}/data")
    js = prerender.exportar_js(site, escudo, actualizado)
    indice = json.loads((site / "data" / "index.json").read_text(encoding="utf-8"))
    anios = [a["anio"] for a in indice["anios"]]
    ultimo = indice["ultimo"]
    ctx = prerender.Contexto(site, js, carpeta_datos, actualizado, escudo, excels_por_anio(site, anios))
    ids = {href: id_ for id_, _, href in js["secciones"]}
    textos = {href: texto for _, texto, href in js["secciones"]}
    paginas_sitemap = []  # (URL absoluta, lastmod) de las páginas cuya canónica es ella misma

    def emitir(destino: str, base: str, plantilla, id_: str, texto: str, vista, anio_url, canonica: str, titulos, fecha: str):
        """Escribe dist/<destino>. `anio_url`: año de la carpeta (None en la raíz); `canonica`: URL canónica; `titulos`: (título, descripción) o None."""
        prefijo = "../" if anio_url is not None else ""
        html = REF_RELATIVA.sub(lambda m: m.group(1) + prefijo + m.group(2), base)
        atributos = f'data-datos="{prefijo}{carpeta_datos}" data-escudo="{prefijo}{escudo}" data-actualizado="{actualizado}" data-raiz="{prefijo}" data-ultimo="{ultimo}"'
        if anio_url is not None:
            atributos += f' data-anio="{anio_url}"'
        html = html.replace('<html lang="es">', f'<html lang="es" {atributos}>', 1)
        html = html.replace(CARGANDO, prerender.montar(vista, id_, plantilla), 1)
        titulo, descripcion = titulos if titulos else (None, None)
        html = seo.poner_cabecera(html, titulo, descripcion, canonica)
        # Migas con el año: las páginas de /<año>/ y los alias de la raíz del último año (que son esa misma página)
        anio_migas = anio_url if anio_url is not None else (vista.anio if id_ in seo.PAGINAS_ANIO and id_ != "inicio" else None)
        url_propia = seo.DOMINIO + destino.removesuffix("index.html")
        extra = seo.precarga(site, dist, vista, manifiesto, id_, html, prefijo) + seo.bloque_jsonld(seo.nodos(id_, texto, canonica, vista, anio_migas))
        html = html.replace("</head>", extra + "</head>", 1)
        (dist / destino).parent.mkdir(parents=True, exist_ok=True)
        (dist / destino).write_text(html, encoding="utf-8")
        manifiesto[destino] = destino
        if canonica == url_propia:
            paginas_sitemap.append((url_propia, fecha))

    for pagina in sorted(site.glob("*.html")):
        html = pagina.read_text(encoding="utf-8")

        def cambia(m):
            ref = m.group(2)
            if ref not in manifiesto:
                raise FileNotFoundError(f"{pagina.name} enlaza {ref}, que no existe en {site}")
            return m.group(1) + manifiesto[ref] + m.group(3)

        html = REF_HTML.sub(cambia, html)
        if '<html lang="es">' not in html:
            raise ValueError(f'{pagina.name}: falta <html lang="es">')
        if pagina.name not in ids:
            raise ValueError(f"{pagina.name} no está en el menú de layout.js (SECCIONES)")
        plantilla = PLANTILLA.search(html)
        html = PLANTILLA.sub("\n", html)
        if CARGANDO not in html:
            raise ValueError(f"{pagina.name}: falta {CARGANDO}")
        plantilla = plantilla.group(1).strip() if plantilla else None
        id_ = ids[pagina.name]
        texto = textos[pagina.name]

        # Raíz: la portada, las páginas sin año y, de las que dependen del año, un alias del último año con la canónica en su carpeta
        if id_ == "inicio":
            canonica = seo.DOMINIO
        elif id_ in seo.PAGINAS_ANIO:
            canonica = seo.DOMINIO + seo.ruta_anio(id_, ultimo)
        else:
            canonica = seo.DOMINIO + pagina.name
        titulos = seo.textos_anio(id_, ultimo) if id_ in seo.PAGINAS_ANIO and id_ != "inicio" else None
        emitir(pagina.name, html, plantilla, id_, texto, ctx.para(None), None, canonica, titulos, lastmod)

        # Una carpeta por año con las páginas que dependen de él
        if id_ in seo.PAGINAS_ANIO:
            for anio in anios:
                canonica = seo.DOMINIO if id_ == "inicio" and anio == ultimo else seo.DOMINIO + seo.ruta_anio(id_, anio)
                fecha = max(fecha_de_git(site, f"{site.name}/data/{anio}"), codigo)
                destino = "index.html" if id_ == "inicio" else pagina.name
                emitir(f"{anio}/{destino}", html, plantilla, id_, texto, ctx.para(anio), anio, canonica, seo.textos_anio(id_, anio), fecha)

    (dist / "404.html").write_text(pagina_404((dist / "index.html").read_text(encoding="utf-8"), ctx.para(None)), encoding="utf-8")
    manifiesto["404.html"] = "404.html"
    (dist / "sitemap.xml").write_text(sitemap(sorted(paginas_sitemap)), encoding="utf-8")
    manifiesto["sitemap.xml"] = "sitemap.xml"

    (dist / "build-manifest.json").write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifiesto


def main(argv):
    site = Path(argv[1]) if len(argv) > 1 else RAIZ / "site"
    dist = Path(argv[2]) if len(argv) > 2 else RAIZ / "dist"
    try:
        manifiesto = build(site, dist)
    except (CicloDeImportaciones, FileNotFoundError, ValueError, prerender.ErrorDePrerender) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"dist/ listo en {dist}: {len(manifiesto)} entradas, datos en {manifiesto['data/']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
