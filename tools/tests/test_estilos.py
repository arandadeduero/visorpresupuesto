"""Estilos de la web: todos los colores son variables, no hay estilos en línea y el CSS generado está al día."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
PAGINAS = sorted(SITE.glob("*.html"))
CSS = sorted((SITE / "css").glob("*.css"))
JS = [p for p in sorted((SITE / "js").glob("*.js")) if not p.name.endswith(".test.js")]

sys.path.insert(0, str(ROOT / "tools"))
import generar_escalas  # noqa: E402

NOMBRES_DE_COLOR = set(
    """aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown burlywood cadetblue
    chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgreen darkgrey
    darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen darkslateblue darkslategray
    darkslategrey darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen
    fuchsia gainsboro ghostwhite gold goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender
    lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey
    lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen
    magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen
    mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite navy oldlace olive olivedrab orange
    orangered orchid palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum powderblue purple
    rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue
    slategray slategrey snow springgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow
    yellowgreen canvas canvastext linktext visitedtext activetext buttonface buttontext field fieldtext highlight highlighttext""".split()
)


def sin_comentarios(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def quitar_bloques_raiz(css: str) -> str:
    """Quita los bloques `:root { … }` (donde se definen los tokens), también los de dentro de @media."""
    salida, i = [], 0
    for m in re.finditer(r":root\s*\{", css):
        if m.start() < i:
            continue
        salida.append(css[i:m.start()])
        nivel, j = 1, m.end()
        while nivel:
            nivel += {"{": 1, "}": -1}.get(css[j], 0)
            j += 1
        i = j
    salida.append(css[i:])
    return "".join(salida)


@pytest.mark.parametrize("ruta", CSS, ids=lambda p: p.name)
def test_fuera_de_los_tokens_no_queda_ningun_literal_de_color(ruta):
    css = quitar_bloques_raiz(sin_comentarios(ruta.read_text(encoding="utf-8")))
    css = re.sub(r"@font-face\s*\{[^}]*\}", "", css)
    valores = re.findall(r":\s*([^;{}]+)(?:;|(?=}))", css)
    for v in valores:
        v = re.sub(r'"[^"]*"|\'[^\']*\'|url\([^)]*\)', "", v)
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b", v), f"{ruta.name}: color hexadecimal en «{v.strip()}»"
        assert not re.search(r"\b(rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\(", v), f"{ruta.name}: color funcional en «{v.strip()}»"
        for palabra in re.findall(r"[a-zA-Z]+", re.sub(r"var\([^)]*\)", "", v)):
            assert palabra.lower() not in NOMBRES_DE_COLOR, f"{ruta.name}: color con nombre «{palabra}» en «{v.strip()}»"


def test_los_unicos_colores_literales_estan_en_los_bloques_de_tokens_de_styles_css():
    # escalas.css (generado) no lleva ningún literal ni siquiera en :root: solo mezcla variables
    escalas = sin_comentarios((SITE / "css" / "escalas.css").read_text(encoding="utf-8"))
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", escalas)
    styles = sin_comentarios((SITE / "css" / "styles.css").read_text(encoding="utf-8"))
    assert re.search(r":root\s*\{[^}]*--rojo:\s*#ce0e2d", styles)
    assert "@media (prefers-color-scheme: dark)" in styles


def test_escalas_css_esta_al_dia():
    actual = (SITE / "css" / "escalas.css").read_text(encoding="utf-8")
    assert actual == generar_escalas.generar(), "ejecuta: python3 tools/generar_escalas.py"
    assert generar_escalas.main(["generar_escalas.py", "--check"]) == 0


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_las_paginas_no_llevan_estilos_en_linea_y_enlazan_escalas(pagina):
    html = pagina.read_text(encoding="utf-8")
    assert not re.search(r"\sstyle\s*=", html, re.I), f"{pagina.name} tiene un atributo style"
    assert "<style" not in html.lower()
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html), f"{pagina.name} tiene un script en línea"
    assert html.index('href="css/styles.css"') < html.index('href="css/escalas.css"')


@pytest.mark.parametrize("ruta", JS, ids=lambda p: p.name)
def test_los_modulos_no_generan_estilos_en_linea_ni_tocan_element_style(ruta):
    js = re.sub(r"(?<!:)//.*", "", ruta.read_text(encoding="utf-8"))  # los comentarios pueden nombrar element.style
    assert not re.search(r"\bstyle\s*=", js), f"{ruta.name}: atributo style en una plantilla"
    assert not re.search(r"\.style\b|setAttribute\(\s*[\"']style|cssText|insertAdjacentHTML\([^)]*style", js), f"{ruta.name}: manipula estilos"
    assert not re.search(r"""["'`]#[0-9a-fA-F]{3,8}["'`]""", js), f"{ruta.name}: escribe un color (deben salir de las variables CSS)"


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_cada_pagina_tiene_politica_de_seguridad_que_impide_estilos_en_linea(pagina):
    html = pagina.read_text(encoding="utf-8")
    csp = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)">', html)
    assert csp, f"{pagina.name} sin Content-Security-Policy"
    politica = {d.split()[0]: d.split()[1:] for d in csp.group(1).split(";") if d.strip()}
    assert politica["style-src"] == ["'self'"]
    assert politica["script-src"] == ["'self'"]
    assert politica["default-src"] == ["'self'"]
    assert "'unsafe-inline'" not in csp.group(1) and "'unsafe-eval'" not in csp.group(1)
    assert politica["object-src"] == ["'none'"]


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_cada_pagina_declara_los_dos_colores_de_tema_y_el_esquema(pagina):
    html = pagina.read_text(encoding="utf-8")
    assert '<meta name="color-scheme" content="light dark">' in html
    assert re.search(r'<meta name="theme-color" content="#[0-9a-f]{6}" media="\(prefers-color-scheme: light\)">', html)
    assert re.search(r'<meta name="theme-color" content="#[0-9a-f]{6}" media="\(prefers-color-scheme: dark\)">', html)
