#!/usr/bin/env python3
"""Construye dist/ a partir de site/ poniendo una huella (hash del contenido) en el nombre de los ficheros estáticos.

Uso: python3 tools/build_site.py [site] [dist]

- css (styles.css, escalas.css), js (módulos incluidos), vendor y tipografías (woff2) se renombran: styles.<huella>.css, home.<huella>.js...
- Los módulos se procesan en orden topológico: su huella sale de su contenido ya con los imports reescritos,
  así un cambio en format.js cambia también la huella de todos los que lo importan (y la de los HTML).
- data/ se copia a data-<huella>/ (huella de todo el directorio) y cada HTML recibe data-datos="data-<huella>/".
- Los HTML y los enlaces entre páginas conservan su nombre.
- dist/build-manifest.json relaciona cada original con su fichero publicado.
"""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

LARGO = 10
IMPORT = re.compile(r'((?:\bfrom|\bimport)\s*)"(\./[^"]+\.js)"')
REF_HTML = re.compile(r'((?:href|src)=")([^"#:]+\.(?:css|js|woff2))(")')
URL_FUENTE = re.compile(r"url\(\.\./(fonts/[^)]+\.woff2)\)")
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

    for rel in sorted(f"vendor/{p.name}" for p in (site / "vendor").glob("*.js")):
        datos = (site / rel).read_bytes()
        nombre = con_huella(rel, huella(datos))
        manifiesto[rel] = nombre
        (dist / nombre).write_bytes(datos)


def build(site: Path, dist: Path) -> dict:
    site, dist = Path(site), Path(dist)
    if dist.exists():
        shutil.rmtree(dist)
    for sub in ["css", "js", "vendor", "fonts"]:
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

    for pagina in sorted(site.glob("*.html")):
        html = pagina.read_text(encoding="utf-8")

        def cambia(m):
            ref = m.group(2)
            if ref not in manifiesto:
                raise FileNotFoundError(f"{pagina.name} enlaza {ref}, que no existe en {site}")
            return m.group(1) + manifiesto[ref] + m.group(3)

        html = REF_HTML.sub(cambia, html)
        html, n = re.subn(r"<html lang=\"es\">", f'<html lang="es" data-datos="{carpeta_datos}">', html, count=1)
        if n != 1:
            raise ValueError(f'{pagina.name}: falta <html lang="es">')
        (dist / pagina.name).write_text(html, encoding="utf-8")
        manifiesto[pagina.name] = pagina.name

    (dist / "build-manifest.json").write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifiesto


def main(argv):
    site = Path(argv[1]) if len(argv) > 1 else RAIZ / "site"
    dist = Path(argv[2]) if len(argv) > 2 else RAIZ / "dist"
    try:
        manifiesto = build(site, dist)
    except (CicloDeImportaciones, FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"dist/ listo en {dist}: {len(manifiesto)} entradas, datos en {manifiesto['data/']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
