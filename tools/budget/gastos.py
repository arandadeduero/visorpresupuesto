"""A3 · Estado de gastos por capítulo, programa y partida."""
import re
from collections import defaultdict

from .common import code_str, find_file, load_sheet, norm, num, sentence_case
from .resumen import parse_resumen
from .labels import AREAS, CAPITULOS_GASTOS, POLITICAS, articulo_gastos

_ROMANOS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9}
_CABECERA = re.compile(r"^capitulo ([ivx]+)$")
_TOTAL = re.compile(r"^total capitulo ([ivx]+)$")


def _es_codigo_programa(v) -> bool:
    if isinstance(v, str):  # «0110» (deuda pública) viene como texto por el cero inicial
        return bool(re.fullmatch(r"\d{4}", v.strip()))
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 1000


def _columna_anterior(rows, year: int) -> int:
    """Posición de la columna del año anterior: la que lleva «año-1» seguida de «año» en la cabecera de un programa.
    Cambia de un ejercicio a otro (en 2024 hay una columna más entre el nombre y los importes)."""
    for row in rows:
        for i in range(len(row) - 1):
            if row[i] == year - 1 and row[i + 1] == year and _es_codigo_programa(row[1]):
                return i
    raise ValueError(f"No se encuentra la cabecera de programa con los años {year - 1} y {year} en A3")


def parse_gastos(year: int) -> dict:
    ws = load_sheet(find_file(year, "A3"), str(year))
    filas = [tuple(r) + (None,) * 8 for r in ws.iter_rows(values_only=True)]
    col = _columna_anterior(filas, year)
    capitulos = {}
    nombres_programa = {}
    partidas = []
    cap = None
    programa = None
    for row in filas:
        prog, econ, nombre, anterior, actual = row[1], row[2], row[3], num(row[col]), num(row[col + 1])
        nombre_txt = nombre.strip() if isinstance(nombre, str) else None

        if nombre_txt and (m := _CABECERA.match(norm(nombre_txt))):
            cap = _ROMANOS[m.group(1).upper()]
            programa = None
        elif nombre_txt and (m := _TOTAL.match(norm(nombre_txt))):
            n = _ROMANOS[m.group(1).upper()]
            corto, oficial = CAPITULOS_GASTOS[n]
            capitulos[n] = {"cap": n, "corto": corto, "oficial": oficial, "anterior": anterior, "actual": actual}
            cap = None
        elif cap is None:
            continue
        elif _es_codigo_programa(prog) and nombre_txt and row[col] == year - 1:
            programa = code_str(prog)
            nombres_programa.setdefault(programa, sentence_case(nombre_txt))
        elif econ is not None and programa is not None:
            partidas.append(
                {"cap": cap, "programa": programa, "codigo": code_str(econ), "nombre": sentence_case(nombre_txt) if nombre_txt else f"Partida {code_str(econ)} (sin descripción)", "anterior": anterior, "actual": actual}
            )

    # Artículos: dos primeros dígitos del código económico («120.03» → 12). Se calculan con todas las partidas,
    # también las del capítulo 1, aunque la web no enseñe su detalle por debajo de programa.
    crudas = list(partidas)
    for p in crudas:
        p["articulo"] = p["codigo"][:2]

    # Capítulo 1: una sola partida por programa con el total.
    personal = defaultdict(lambda: [0.0, 0.0])
    for p in partidas:
        if p["cap"] == 1:
            personal[p["programa"]][0] += p["anterior"] or 0
            personal[p["programa"]][1] += p["actual"] or 0
    resto = [p for p in partidas if p["cap"] != 1]
    agrupadas = [
        {"cap": 1, "programa": prog, "codigo": None, "articulo": None, "nombre": "Gastos de personal", "anterior": round(a, 2), "actual": round(b, 2)}
        for prog, (a, b) in personal.items()
    ]
    partidas = agrupadas + resto

    # La columna del año anterior de A3 no siempre está completa (p. ej. no recoge las inversiones del año anterior).
    # Se compara cada capítulo con los «créditos» del año anterior de A1; si no cuadra, esas partidas quedan sin
    # año anterior (null) en lugar de enseñar variaciones falsas. Los capítulos usan siempre la cifra de A1.
    ref = {c["cap"]: c["anterior"] for c in parse_resumen(year)["gastosPorCapitulo"]}
    sin_anterior = []
    for n in sorted(capitulos):
        suma = sum(p["anterior"] or 0 for p in partidas if p["cap"] == n)
        if abs(suma - (ref.get(n) or 0)) > max(1.0, 0.05 * abs(ref.get(n) or 0)):
            sin_anterior.append(n)
        capitulos[n]["anterior"] = ref.get(n, capitulos[n]["anterior"])
    for p in partidas:
        p["anterior"] = None if p["cap"] in sin_anterior else (p["anterior"] or 0.0)

    articulos = []
    for cap_n, cod in sorted({(p["cap"], p["articulo"]) for p in crudas}):
        propios = [p for p in crudas if p["cap"] == cap_n and p["articulo"] == cod]
        nombre, oficial = articulo_gastos(cod)
        articulos.append(
            {
                "cap": cap_n,
                "codigo": cod,
                "nombre": nombre,
                "oficial": oficial,
                "anterior": None if cap_n in sin_anterior else round(sum(p["anterior"] or 0 for p in propios), 2),
                "actual": round(sum(p["actual"] or 0 for p in propios), 2),
            }
        )

    def suma_anterior(items):
        return None if any(x["anterior"] is None for x in items) else round(sum(x["anterior"] for x in items), 2)

    por_programa = defaultdict(list)
    for p in partidas:
        por_programa[p["programa"]].append(p)
    programas = [
        {
            "codigo": cod,
            "nombre": nombres_programa.get(cod, f"Programa {cod}"),
            "area": int(cod[0]),
            "politica": cod[:2],
            "anterior": suma_anterior(items),
            "actual": round(sum(x["actual"] or 0 for x in items), 2),
        }
        for cod, items in sorted(por_programa.items())
    ]
    politicas = []
    for codigo in sorted({p["politica"] for p in programas}):
        propios = [p for p in programas if p["politica"] == codigo]
        politicas.append(
            {
                "codigo": codigo,
                "nombre": POLITICAS.get(codigo, f"Política {codigo}"),
                "area": int(codigo[0]),
                "anterior": suma_anterior(propios),
                "actual": round(sum(p["actual"] for p in propios), 2),
            }
        )
    usadas = sorted({p["area"] for p in programas})
    return {
        "anio": year,
        "capitulos": [capitulos[n] for n in sorted(capitulos)],
        "sinAnterior": sin_anterior,
        "articulos": articulos,
        "areas": [{"area": a, "nombre": AREAS[a]} for a in usadas],
        "politicas": politicas,
        "programas": programas,
        "partidas": partidas,
    }
