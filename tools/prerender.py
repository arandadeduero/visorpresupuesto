"""Contenido estático de cada página (prerender), para quien no ejecuta JavaScript.

El navegador, al cargar el JS, sustituye todo el <body> por lo que pinta cada página; mientras tanto (y para los
rastreadores, las vistas previas y quien tenga el JS desactivado) el HTML ya trae el marco y las cifras clave del
último año en tablas simples. Todo texto con cifras sale de site/data/<último>/*.json; el marco, los enlaces
«Relacionado», las tarjetas de la portada, los avisos sobre préstamos y los indicadores los calcula el propio JS de la
web (tools/exportar_js.mjs), así que no hay una segunda copia en Python.
"""
import html
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from urllib.parse import quote

NBSP = " "
REPO = "https://github.com/arandadeduero/visorpresupuesto"
ORDEN_JSON = ["resumen", "ingresos", "gastos", "inversiones", "subvenciones", "deuda"]
NOMBRE_JSON = {
    "resumen": ("Resumen", "Totales, ingresos y gastos por capítulo, reparto por cada 100 € y población."),
    "ingresos": ("Ingresos", "Capítulos y conceptos de ingreso, con el año anterior."),
    "gastos": ("Gastos", "Capítulos, políticas, programas y partidas."),
    "inversiones": ("Inversiones", "Proyectos por programa y cómo se financian."),
    "subvenciones": ("Subvenciones", "Subvenciones nominativas por actividad y por entidad."),
    "deuda": ("Deuda", "Préstamos, deuda viva por año, préstamo previsto y carga financiera."),
}


class ErrorDePrerender(Exception):
    pass


# ---------------------------------------------------------------- formato (igual que site/js/format.js)

def esc(texto) -> str:
    return html.escape("" if texto is None else str(texto), quote=True)


def _redondea(n: float) -> int:
    return int(abs(n) + 0.5) * (1 if n >= 0 else -1)


def _agrupa(n: float) -> str:
    return f"{_redondea(n):,}".replace(",", ".")


def euros(n, compacto: bool = False) -> str:
    if n is None:
        return "—"
    if compacto and abs(n) >= 1_000_000:
        v = f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{v}{NBSP}M€"
    return f"{_agrupa(n)}{NBSP}€"


def porcentaje(n) -> str:
    return "—" if n is None else f"{n:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " %"


def fecha_larga(iso: str) -> str:
    anio, mes, dia = (int(x) for x in iso.split("-"))
    meses = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
    return f"{dia} de {meses[mes - 1]} de {anio}"


def id_termino(termino: str) -> str:
    """Misma regla que idTermino() de site/js/format.js (ancla de cada término de la guía)."""
    return re.sub(r"[^a-z]+", "-", unicodedata.normalize("NFD", termino.lower()))


def etiqueta_capitulo(c: dict) -> str:
    return f"Cap {c['cap']} - {c['corto']}"


# ---------------------------------------------------------------- piezas de HTML

def tabla(cabeceras: list, filas: list, pie: list | None = None) -> str:
    """Tabla con las mismas clases que tablaHtml() de site/js/ui.js. cabeceras: [(texto, es_numerica)]; filas: celdas ya en HTML."""
    def clase(i):
        return ' class="num"' if cabeceras[i][1] else ""

    def fila(celdas, th=False):
        tag = "th" if th else "td"
        return "<tr>" + "".join(f"<{tag}{clase(i)}>{c}</{tag}>" for i, c in enumerate(celdas)) + "</tr>"

    cab = "".join(f"<th{clase(i)}>{esc(t)}</th>" for i, (t, _) in enumerate(cabeceras))
    cuerpo = "".join(fila(f) for f in filas) + (fila(pie, th=True) if pie else "")
    return f'<div class="tabla-scroll"><table class="datos"><thead><tr>{cab}</tr></thead><tbody>{cuerpo}</tbody></table></div>'


def titulo(texto: str, anio=None) -> str:
    return f"<h1>{texto}" + (f' <span class="muted">{anio}</span>' if anio else "") + "</h1>"


def sin_anio(fragmento: str) -> str:
    """Los avisos del JS enlazan con ?anio=AAAA; en el HTML estático las URLs van limpias."""
    return re.sub(r"\?anio=\d{4}", "", fragmento)


# ---------------------------------------------------------------- contexto

class Contexto:
    """Todo lo que necesita el prerender: datos del último año, lo que exporta el JS y las rutas con huella."""

    def __init__(self, site: Path, js: dict, carpeta_datos: str, actualizado: str, escudo: str, excels: dict | None = None):
        self.site = Path(site)
        self.js = js
        self.carpeta_datos = carpeta_datos
        self.actualizado = actualizado
        self.escudo = escudo
        self.excels = excels or {}
        self.indice = json.loads((self.site / "data" / "index.json").read_text(encoding="utf-8"))
        self.ultimo = self.indice["ultimo"]
        self.anios = [a["anio"] for a in self.indice["anios"]]
        self.terminos = json.loads((self.site / "data" / "guia-terminos.json").read_text(encoding="utf-8"))

    def datos(self, nombre: str, anio: int | None = None) -> dict:
        anio = anio or self.ultimo
        return json.loads((self.site / "data" / str(anio) / f"{nombre}.json").read_text(encoding="utf-8"))

    def relacionado(self, pagina: str) -> str:
        return sin_anio(self.js["relacionados"].get(pagina, ""))

    def url_json(self, anio: int, nombre: str) -> str:
        return f"{self.carpeta_datos}{anio}/{nombre}.json"


def exportar_js(site: Path, escudo: str, actualizado: str) -> dict:
    """Ejecuta tools/exportar_js.mjs (node) y devuelve lo que saca de los módulos de la web."""
    guion = Path(__file__).resolve().parent / "exportar_js.mjs"
    try:
        r = subprocess.run(["node", str(guion), str(site), escudo, actualizado], capture_output=True, text=True, encoding="utf-8")
    except FileNotFoundError as e:
        raise ErrorDePrerender("Hace falta node para construir la web (el HTML estático reutiliza el JS): https://nodejs.org") from e
    if r.returncode != 0:
        raise ErrorDePrerender(f"tools/exportar_js.mjs ha fallado:\n{r.stderr}")
    return json.loads(r.stdout)


# ---------------------------------------------------------------- una función por página

NOSCRIPT = (
    '<noscript><div class="aviso"><strong>Esta página funciona mejor con JavaScript.</strong>'
    "<p>Con JavaScript puedes elegir el año, ver gráficos, buscar y ordenar las tablas. Sin él ves las cifras principales del "
    "presupuesto de {anio} en tablas. Puedes <a href=\"descargas.html\">descargar todos los datos</a> o consultar los "
    f'<a href="{REPO}" rel="noopener">Excel originales del Ayuntamiento</a>.</p></div></noscript>'
)


def _intro(ctx, parrafo: str) -> str:
    return f'<p class="lead">{parrafo}</p>' + NOSCRIPT.format(anio=ctx.ultimo)


def _filas_capitulos(caps: list) -> list:
    return [[esc(etiqueta_capitulo(c)), euros(c.get("anterior")), euros(c["actual"])] for c in caps]


def _cab_capitulos(anio: int) -> list:
    return [("Capítulo", False), (str(anio - 1), True), (str(anio), True)]


def pagina_inicio(ctx: Contexto) -> str:
    r = ctx.datos("resumen")
    anio = ctx.ultimo
    filas = [[esc(b["bloque"]), f"{b['euros']}{NBSP}€", euros(b["importe"])] for b in r["por100"]]
    return (
        f"<h1>Por cada 100{NBSP}€ que gasta el Ayuntamiento en {anio}…</h1>"
        + _intro(ctx, f"El Ayuntamiento de Aranda de Duero prevé gastar <strong>{euros(r['totalGastos'])}</strong> en {anio} (presupuesto inicial). Así se reparte cada 100{NBSP}€: personal, servicios, obras y otros gastos, como la deuda.")
        + tabla([("En qué", False), ("Por cada 100 €", True), (f"Importe en {anio}", True)], filas)
        + f'<p><a href="gastos.html">Ver el detalle de los gastos del Ayuntamiento por política</a></p>'
        + "<h2>Para cada vecino</h2>"
        + f'<p class="lead">El presupuesto de {anio} equivale a unos <strong>{euros(r["totalGastos"] / r["habitantes"])}</strong> por habitante al año ({_agrupa(r["habitantes"])} habitantes).</p>'
        + f'<p class="muted">Es el gasto previsto del Ayuntamiento dividido entre la población ({esc(r["fuentePoblacion"])}). No es lo que paga cada vecino: ni los impuestos se reparten por igual ni todo el gasto se paga con ellos.</p>'
        + "<h2>Y además…</h2>"
        + sin_anio(ctx.js["tarjetasInicio"])
        + '<p class="muted">Es el presupuesto inicial: lo que el Ayuntamiento prevé gastar, no lo gastado hasta hoy.</p>'
    )


def pagina_resumen(ctx: Contexto) -> str:
    r = ctx.datos("resumen")
    anio = ctx.ultimo
    equilibrado = abs(r["totalIngresos"] - r["totalGastos"]) < 1
    return (
        titulo(f"Resumen del presupuesto {anio}")
        + _intro(ctx, f"El Ayuntamiento prevé ingresar <strong>{euros(r['totalIngresos'])}</strong> y gastar <strong>{euros(r['totalGastos'])}</strong>{': el presupuesto está equilibrado' if equilibrado else ''}.")
        + "<h2>De dónde sale el dinero</h2>"
        + tabla(_cab_capitulos(anio), _filas_capitulos(r["ingresosPorCapitulo"]), ["Total", euros(sum(c.get("anterior") or 0 for c in r["ingresosPorCapitulo"])), euros(r["totalIngresos"])])
        + "<h2>En qué se gasta</h2>"
        + tabla(_cab_capitulos(anio), _filas_capitulos(r["gastosPorCapitulo"]), ["Total", euros(r["totalGastosAnterior"]), euros(r["totalGastos"])])
        + f'<p class="muted">La cifra de {anio - 1} son los créditos del presupuesto de {anio - 1}.</p>'
    )


def pagina_ingresos(ctx: Contexto) -> str:
    d = ctx.datos("ingresos")
    anio = ctx.ultimo
    total = sum(c["actual"] for c in d["capitulos"])
    caps = sorted(d["capitulos"], key=lambda c: -c["actual"])
    filas = [[esc(etiqueta_capitulo(c)), euros(c.get("anterior")), euros(c["actual"]), porcentaje(c["actual"] / total * 100)] for c in caps]
    return (
        titulo("¿De dónde sale el dinero?", anio)
        + _intro(ctx, f"Ingresos previstos: <strong>{euros(total)}</strong>. Los ingresos se agrupan en capítulos (impuestos, tasas, transferencias de otras administraciones, préstamos…) y cada capítulo, en artículos y conceptos.")
        + tabla([("Capítulo", False), (str(anio - 1), True), (str(anio), True), ("% del total", True)], filas)
    )


def pagina_gastos(ctx: Contexto) -> str:
    d = ctx.datos("gastos")
    anio = ctx.ultimo
    total = sum(c["actual"] for c in d["capitulos"])
    pols = sorted((p for p in d["politicas"] if p["actual"] > 0), key=lambda p: -p["actual"])
    filas_pol = [[esc(p["nombre"]), euros(p.get("anterior")), euros(p["actual"]), porcentaje(p["actual"] / total * 100)] for p in pols]
    return (
        titulo("¿En qué se gasta el dinero?", anio)
        + _intro(ctx, f"Total previsto: <strong>{euros(total)}</strong>. Los gastos se pueden ver por tipo de gasto (capítulos) o por la política a la que sirven (cultura, seguridad, limpieza…).")
        + "<h2>Por tipo de gasto</h2>"
        + tabla(_cab_capitulos(anio), _filas_capitulos(d["capitulos"]))
        + "<h2>Por política de gasto</h2>"
        + tabla([("Política", False), (str(anio - 1), True), (str(anio), True), ("% del total", True)], filas_pol)
    )


def pagina_inversiones(ctx: Contexto) -> str:
    d = ctx.datos("inversiones")
    anio = ctx.ultimo
    nombres = {"prestamo": "Préstamo", "ingresosCorrientes": "Ingresos del Ayuntamiento", "otros": "Otros", "rta": "Remanente de tesorería", "subvenciones": "Subvenciones"}
    fuentes = [[esc(n), euros(d["fuentes"][k]), porcentaje(d["fuentes"][k] / d["total"] * 100)] for k, n in nombres.items() if d["fuentes"].get(k, 0) > 0]
    programas = sorted(d["programas"], key=lambda p: -p["total"])
    filas = [[esc(p["nombre"]), str(len(p["proyectos"])), euros(p["total"])] for p in programas]
    return (
        titulo("Inversiones: obras y compras", anio)
        + _intro(ctx, f"El Ayuntamiento prevé invertir <strong>{euros(d['total'])}</strong> en obras, equipamientos y mejoras en {anio}.")
        + "<h2>¿Cómo se pagan?</h2>"
        + tabla([("Fuente", False), ("Importe", True), ("% del total", True)], fuentes)
        + sin_anio(ctx.js["avisos"]["inversiones"])
        + "<h2>¿En qué se invierte?</h2>"
        + tabla([("Programa", False), ("Proyectos", True), ("Importe", True)], filas)
    )


def pagina_subvenciones(ctx: Contexto) -> str:
    d = ctx.datos("subvenciones")
    anio = ctx.ultimo
    progs = sorted(d["programas"], key=lambda p: -p["actual"])
    filas = [[esc(p["programa"] + (" (cuotas)" if p["bloque"] == "cuotas" else "")), str(len(p["items"])), euros(p.get("anterior")), euros(p["actual"])] for p in progs]
    return (
        titulo("Subvenciones", anio)
        + _intro(ctx, f"El Ayuntamiento prevé dar <strong>{euros(d['total'])}</strong> a asociaciones y entidades por convenio o cuota (en {anio - 1}: {euros(d['totalAnterior'])}).")
        + tabla([("Actividad", False), ("Entidades", True), (str(anio - 1), True), (str(anio), True)], filas)
    )


def pagina_deuda(ctx: Contexto) -> str:
    d = ctx.datos("deuda")
    anio = ctx.ultimo
    viva_inicio = sum(p["vivaInicio"] for p in d["prestamos"])
    filas_serie = [[str(s["anio"]), euros(s["viva"])] for s in d["serie"]]
    filas_prestamos = [[esc(p["entidad"]), euros(p["importe"]), esc(p["tipoInteres"]), esc(p["ultimaAmortizacion"].split("-")[0]), euros(p["vivaFin"])] for p in d["prestamos"]]
    carga = d["carga"]
    return (
        titulo("Deuda del Ayuntamiento", anio)
        + _intro(ctx, f"El Ayuntamiento deberá a los bancos <strong>{euros(d['titular']['vivaFin'])}</strong> a 31 de diciembre de {anio}, con los préstamos que ya tiene. A 1 de enero era de {euros(viva_inicio)}: durante el año devuelve {euros(carga['amortizacion'])}.")
        + sin_anio(ctx.js["avisos"]["deuda"])
        + "<h2>Cómo evoluciona la deuda actual</h2>"
        + tabla([("Final de año", False), ("Deuda", True)], filas_serie)
        + "<h2>Los préstamos actuales</h2>"
        + tabla([("Entidad", False), ("Importe pedido", True), ("Interés", False), ("Último año de pago", False), (f"Queda por pagar a 31/12/{anio}", True)], filas_prestamos)
        + f"<h2>Cuánto cuesta la deuda en {anio}</h2>"
        + f"<p>La carga financiera es lo que se paga cada año por los préstamos: <strong>{euros(carga['total'])}</strong> en total, de los cuales {euros(carga['amortizacion'])} son devolución del dinero prestado y {euros(carga['intereses'])} son intereses.</p>"
    )


def pagina_comparar(ctx: Contexto) -> str:
    filas = []
    for a in ctx.anios:
        r = ctx.datos("resumen", a)
        filas.append([str(a), euros(r["totalIngresos"]), euros(r["totalGastos"]), euros(r["totalGastos"] / r["habitantes"])])
    return (
        titulo("Comparar presupuestos")
        + _intro(ctx, "Elige dos presupuestos y mira qué ha cambiado entre uno y otro: gastos por política y por capítulo, ingresos por capítulo e indicadores. Estos son los totales de cada año publicado.")
        + tabla([("Año", False), ("Ingresos previstos", True), ("Gastos previstos", True), ("Gasto por habitante", True)], filas)
        + '<p class="muted">Los importes son euros corrientes, sin ajustar por la subida de precios. Más en la <a href="guia.html">guía</a> y en la <a href="metodologia.html">metodología</a>.</p>'
    )


def pagina_indicadores(ctx: Contexto) -> str:
    i = ctx.js["indicadores"]
    anio = ctx.ultimo
    filas = [
        ["Impuestos y tasas por habitante", euros(i["impuestosYTasasPorHabitante"])],
        ["Ahorro bruto", f"{euros(i['ahorroBruto'], True)} ({porcentaje(i['ahorroBrutoPct'])} de los ingresos corrientes)"],
        ["Deuda por habitante", euros(i["deudaPorHabitante"])],
        ["Nivel de endeudamiento (estimado)", porcentaje(i["deudaSobreIngresosCorrientesPct"])],
        ["Ahorro neto (estimado)", f"{euros(i['ahorroNetoEstimado'], True)} ({porcentaje(i['ahorroNetoEstimadoPct'])} de los ingresos)"],
        ["Lo que cuesta la deuda al año", f"{euros(i['cargaFinanciera'], True)} ({porcentaje(i['cargaFinancieraPct'])} de los ingresos)"],
        ["Dependencia de otras administraciones", porcentaje(i["dependenciaTransferenciasPct"])],
    ]
    return (
        titulo("Indicadores", anio)
        + _intro(ctx, "Siete cifras sencillas para entender la situación económica del Ayuntamiento, calculadas con las cifras del presupuesto inicial.")
        + tabla([("Indicador", False), (f"Valor en {anio}", True)], [[esc(a), b] for a, b in filas])
        + f"<h2>Nivel de endeudamiento</h2><p>{esc(ctx.js['textoNivelEndeudamiento'])}</p>"
        + '<p class="muted">No son los indicadores oficiales de la liquidación del presupuesto. Más explicaciones en la <a href="guia.html">guía</a> y en la <a href="metodologia.html">metodología</a>.</p>'
    )


def pagina_calculadora(ctx: Contexto) -> str:
    return (
        titulo("¿A qué se destina lo que pago?", ctx.ultimo)
        + _intro(ctx, "Parte del presupuesto se financia con impuestos y tasas locales. Escribe lo que pagas al año (mira tus recibos del IBI, del impuesto de vehículos y de las tasas) y verás cómo se repartiría en los gastos del Ayuntamiento.")
        + '<div class="aviso"><h3>Cómo leerlo</h3><p>Es un reparto <strong>proporcional y orientativo</strong>: los impuestos no se destinan a un servicio concreto, sino al conjunto del presupuesto. Aquí se reparte tu aportación en la misma proporción que el gasto previsto de cada política. Tampoco todo el gasto se paga con impuestos locales: también hay transferencias de otras administraciones y préstamos.</p></div>'
        + '<p>La calculadora necesita JavaScript. Mientras tanto, mira <a href="gastos.html">en qué se gasta el dinero del Ayuntamiento por política</a> y <a href="ingresos.html">de dónde sale</a>.</p>'
    )


def pagina_guia(ctx: Contexto) -> str:
    items = "".join(
        f'<dt id="{esc(id_termino(t["termino"]))}">{esc(t["termino"])}</dt><dd>{esc(t["definicion"])}'
        + (f' <a href="{esc(t["enlace"]["url"])}" rel="noopener">{esc(t["enlace"]["texto"])}</a>.' if t.get("enlace") else "")
        + "</dd>"
        for t in ctx.terminos
    )
    return (
        "<h1>Guía: las palabras del presupuesto</h1>"
        + '<p class="lead">Qué significan los términos que verás en esta web.</p>'
        + f'<dl class="glosario">{items}</dl>'
        + f'<p class="muted">¿Echas en falta alguna palabra? <a href="{REPO}/issues" rel="noopener">Cuéntanoslo</a>. Para ver los datos, vuelve al <a href="./">inicio</a>.</p>'
    )


def pagina_descargas(ctx: Contexto) -> str:
    anio = ctx.ultimo
    bloques = []
    for a in sorted(ctx.anios, reverse=True):
        lista = "".join(
            f'<li><a href="{esc(ctx.url_json(a, f))}" download>{esc(NOMBRE_JSON[f][0])} {a} ({f}.json)</a><br><span class="muted">{esc(NOMBRE_JSON[f][1])}</span></li>'
            for f in ORDEN_JSON
        )
        excels = "".join(
            f'<li><a href="{esc(url_excel(a, n))}" rel="noopener">{esc(n)}</a></li>' for n in ctx.excels.get(a, [])
        )
        bloques.append(
            f"<h2>Presupuesto {a}</h2><h3>Datos en formato JSON</h3><ul class=\"descargas\">{lista}</ul>"
            + (f'<h3>Excel originales del Ayuntamiento</h3><ul class="descargas">{excels}</ul>' if excels else "")
        )
    return (
        titulo("Descargas")
        + _intro(ctx, "Los datos que alimentan esta web, para que puedas usarlos, revisarlos o compararlos: ficheros JSON de cada año y los Excel originales que publicó el Ayuntamiento.")
        + "".join(bloques)
        + f'<p>Todos los Excel están también en el <a href="{REPO}/tree/main/{anio}" rel="noopener">repositorio del proyecto</a>.</p>'
        + '<p class="muted">Los importes son del presupuesto inicial. Las cifras «por habitante» usan la población indicada en la página de resumen.</p>'
    )


def url_excel(anio: int, nombre: str) -> str:
    return f"{REPO}/raw/main/{anio}/{quote(nombre)}"


PAGINAS = {
    "inicio": pagina_inicio, "resumen": pagina_resumen, "ingresos": pagina_ingresos, "gastos": pagina_gastos,
    "inversiones": pagina_inversiones, "subvenciones": pagina_subvenciones, "deuda": pagina_deuda,
    "comparar": pagina_comparar, "indicadores": pagina_indicadores, "calculadora": pagina_calculadora,
    "guia": pagina_guia, "descargas": pagina_descargas,
}


def contenido_pagina(ctx: Contexto, pagina: str, estatico: str | None = None) -> str:
    """HTML de <main> para una página. `estatico` es el contenido de la <template> de las páginas que son solo texto (metodología)."""
    if pagina in PAGINAS:
        cuerpo = PAGINAS[pagina](ctx)
    elif estatico is not None:
        cuerpo = estatico
    else:
        raise ErrorDePrerender(f"No sé prerenderizar la página «{pagina}»")
    if "<noscript>" not in cuerpo:  # las páginas que son solo texto lo llevan al final
        cuerpo += NOSCRIPT.format(anio=ctx.ultimo)
    return cuerpo + ctx.relacionado(pagina)


def montar(ctx: Contexto, pagina: str, estatico: str | None = None) -> str:
    """Marco completo (cabecera, menú, contenido y pie) para sustituir el «Cargando…» del HTML fuente."""
    return ctx.js["marcos"][pagina].replace(ctx.js["marca"], contenido_pagina(ctx, pagina, estatico))
