"""A2 · Estado de ingresos por capítulo y concepto."""
import re

from .common import code_str, find_file, load_sheet, num, sentence_case
from .labels import CAPITULOS_INGRESOS

_ROMANOS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9}
_CABECERA = re.compile(r"^CAPÍTULO ([IVX]+)\b")
_TOTAL = re.compile(r"^TOTAL CAPÍTULO ([IVX]+)\b")


def parse_ingresos(year: int) -> dict:
    ws = load_sheet(find_file(year, "A2"), str(year))
    capitulos = {}
    actual = None
    for row in ws.iter_rows(values_only=True):
        row = tuple(row) + (None,) * (6 - len(row))
        codigo, nombre = row[1], row[2]
        if not isinstance(nombre, str):
            continue
        nombre = nombre.strip()
        if m := _CABECERA.match(nombre):
            n = _ROMANOS[m.group(1)]
            corto, oficial = CAPITULOS_INGRESOS[n]
            actual = {"cap": n, "corto": corto, "oficial": oficial, "y2024": None, "y2025": None, "y2026": None, "conceptos": []}
            capitulos[n] = actual
        elif m := _TOTAL.match(nombre):
            c = capitulos[_ROMANOS[m.group(1)]]
            c["y2024"], c["y2025"], c["y2026"] = num(row[3]), num(row[4]), num(row[5])
        elif actual is not None and codigo is not None and not nombre.upper().startswith("ARTÍCULO"):
            if isinstance(codigo, str) and not codigo.strip()[:1].isdigit():
                continue
            actual["conceptos"].append(
                {
                    "codigo": code_str(codigo),
                    "nombre": sentence_case(nombre),
                    "y2024": num(row[3]),
                    "y2025": num(row[4]),
                    "y2026": num(row[5]),
                }
            )
    return {"anio": year, "capitulos": [capitulos[n] for n in sorted(capitulos)]}
