"""A3 · Estado de gastos por capítulo, programa y partida."""
import re
from collections import defaultdict

from .common import code_str, find_file, load_sheet, num, sentence_case
from .labels import AREAS, CAPITULOS_GASTOS

_ROMANOS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9}
_CABECERA = re.compile(r"^CAPÍTULO ([IVX]+)$")
_TOTAL = re.compile(r"^TOTAL CAPÍTULO ([IVX]+)$")


def _es_codigo_programa(v) -> bool:
    if isinstance(v, str):  # «0110» (deuda pública) viene como texto por el cero inicial
        return bool(re.fullmatch(r"\d{4}", v.strip()))
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 1000


def parse_gastos(year: int) -> dict:
    ws = load_sheet(find_file(year, "A3"), str(year))
    capitulos = {}
    nombres_programa = {}
    partidas = []
    cap = None
    programa = None
    for row in ws.iter_rows(values_only=True):
        row = tuple(row) + (None,) * (6 - len(row))
        prog, econ, nombre, y2025, y2026 = row[1], row[2], row[3], num(row[4]), num(row[5])
        nombre_txt = nombre.strip() if isinstance(nombre, str) else None

        if nombre_txt and (m := _CABECERA.match(nombre_txt)):
            cap = _ROMANOS[m.group(1)]
            programa = None
        elif nombre_txt and (m := _TOTAL.match(nombre_txt)):
            n = _ROMANOS[m.group(1)]
            corto, oficial = CAPITULOS_GASTOS[n]
            capitulos[n] = {"cap": n, "corto": corto, "oficial": oficial, "y2025": y2025, "y2026": y2026}
            cap = None
        elif cap is None:
            continue
        elif _es_codigo_programa(prog) and nombre_txt and row[4] == 2025.0:
            programa = code_str(prog)
            nombres_programa.setdefault(programa, sentence_case(nombre_txt))
        elif econ is not None and programa is not None:
            partidas.append(
                {"cap": cap, "programa": programa, "codigo": code_str(econ), "nombre": sentence_case(nombre_txt) if nombre_txt else f"Partida {code_str(econ)} (sin descripción)", "y2025": y2025, "y2026": y2026}
            )

    # Capítulo 1: una sola partida por programa con el total.
    personal = defaultdict(lambda: [0.0, 0.0])
    for p in partidas:
        if p["cap"] == 1:
            personal[p["programa"]][0] += p["y2025"] or 0
            personal[p["programa"]][1] += p["y2026"] or 0
    resto = [p for p in partidas if p["cap"] != 1]
    agrupadas = [
        {"cap": 1, "programa": prog, "codigo": None, "nombre": "Gastos de personal", "y2025": round(a, 2), "y2026": round(b, 2)}
        for prog, (a, b) in personal.items()
    ]
    partidas = agrupadas + resto

    totales = defaultdict(lambda: [0.0, 0.0])
    for p in partidas:
        totales[p["programa"]][0] += p["y2025"] or 0
        totales[p["programa"]][1] += p["y2026"] or 0
    programas = [
        {
            "codigo": cod,
            "nombre": nombres_programa.get(cod, f"Programa {cod}"),
            "area": int(cod[0]),
            "y2025": round(t[0], 2),
            "y2026": round(t[1], 2),
        }
        for cod, t in sorted(totales.items())
    ]
    usadas = sorted({p["area"] for p in programas})
    return {
        "anio": year,
        "capitulos": [capitulos[n] for n in sorted(capitulos)],
        "areas": [{"area": a, "nombre": AREAS[a]} for a in usadas],
        "programas": programas,
        "partidas": partidas,
    }
