"""A9 · Anexo de inversiones reales: proyectos y su financiación."""
import re

from .common import code_str, find_file, load_sheet, norm, num, sentence_case

FUENTES = ("prestamo", "ingresosCorrientes", "otros", "rta", "subvenciones")
# Cómo empieza el rótulo de cada fuente de financiación (sin tildes ni mayúsculas): «SUBVENC.» en 2024, «SUBVENCIONES» después;
# el remanente es «RTA (CAP 8)» o «REMANENTE DE TESORERÍA AFECTADO (CAP 8)»
_ROTULOS = {"prestamo": "prestamo", "ingresosCorrientes": "ingresos corrientes", "otros": "otros", "rta": ("rta", "remanente"), "subvenciones": "subvenc"}


def _es_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _columnas(filas) -> dict:
    """Posición de cada columna según la cabecera: cambia entre ejercicios (2024 empieza en la columna A; 2027 añade
    «Part. Ciud.» y una columna de iconos)."""
    for fila in filas:
        etiquetas = [norm(v) if isinstance(v, str) else "" for v in fila]
        codigo = next((i for i, e in enumerate(etiquetas) if e.startswith("partida")), None)
        if codigo is None:
            continue
        proyecto = [i for i, e in enumerate(etiquetas) if e == "proyecto"]
        importe = etiquetas.index("importe") if "importe" in etiquetas else proyecto[1]  # 2026 y 2027: el segundo «PROYECTO»
        cols = {"codigo": codigo, "nombre": proyecto[0], "importe": importe, "total": etiquetas.index("total")}
        for campo, rotulo in _ROTULOS.items():
            cols[campo] = next(i for i, e in enumerate(etiquetas) if e.startswith(rotulo))
        return cols
    raise ValueError("No se encuentra la cabecera «PARTIDA/CÓDIGO» en A9")


def parse_inversiones(year: int) -> dict:
    ws = load_sheet(find_file(year, "A9"), str(year))
    filas = [tuple(r) for r in ws.iter_rows(values_only=True)]
    cols = _columnas(filas)
    programas = []
    programa = None
    partida = None
    total = None
    fuentes = None
    for row in filas:
        row = row + (None,) * 15
        codigo, nombre = row[cols["codigo"]], row[cols["nombre"]]
        if isinstance(nombre, str) and norm(nombre).startswith("total capitulo vi"):
            total = num(row[cols["total"]])
            fuentes = {f: num(row[cols[f]]) or 0.0 for f in FUENTES}
            break
        cod = code_str(codigo)
        es_texto = isinstance(nombre, str) and not nombre.strip().isdigit()  # «1330» a secas = subtotal
        if cod and es_texto and re.fullmatch(r"\d{4}", cod):  # cabecera de programa
            programa = {"codigo": cod, "nombre": sentence_case(nombre), "total": 0.0, "proyectos": []}
            # Si un programa aparece dos veces (en A9 2025, «9240» deja un bloque antiguo duplicado antes del bueno,
            # que sí coincide con A3 y con el total del capítulo), vale el último bloque.
            programas = [x for x in programas if x["codigo"] != cod]
            programas.append(programa)
            partida = None
        elif cod and es_texto and re.fullmatch(r"\d{3}", cod):  # cabecera de partida económica (622, 650…)
            partida = cod
        elif es_texto and _es_num(row[cols["importe"]]) and programa is not None:  # proyecto (a veces con código propio, p. ej. «005/2023»)
            proyecto = {"nombre": nombre.strip(), "partida": partida}
            for campo in ("importe", *FUENTES):
                proyecto[campo] = num(row[cols[campo]]) or 0.0
            programa["proyectos"].append(proyecto)
            programa["total"] = round(programa["total"] + proyecto["importe"], 2)
    return {
        "anio": year,
        "total": total,
        "fuentes": fuentes,
        "programas": [p for p in programas if p["proyectos"]],
    }
