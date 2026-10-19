"""A2 · Estado de ingresos por capítulo y concepto."""
import re

from .common import code_str, find_file, load_sheet, norm, num, sentence_case
from .labels import CAPITULOS_INGRESOS

_ROMANOS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9}
_CABECERA = re.compile(r"^capitulo ([ivx]+)\b")
_TOTAL = re.compile(r"^total capitulo ([ivx]+)\b")
_ANIO = re.compile(r"^ano (\d{4})$")


def _columnas(row, year: int) -> dict:
    """Posición de cada año en una cabecera de capítulo. Según el ejercicio hay dos o tres columnas
    («AÑO 2024», «AÑO 2025»…) y en 2024 la del año anterior se llama «PREVISIONES»."""
    cols = {}
    for i, v in enumerate(row):
        if i < 3 or not isinstance(v, str):
            continue
        if m := _ANIO.match(norm(v)):
            cols[int(m.group(1))] = i
        elif norm(v) == "previsiones":
            cols[year - 1] = i
    if year not in cols:
        raise ValueError(f"La cabecera de A2 no tiene la columna del año {year}: {row}")
    return {"actual": cols[year], "anterior": cols.get(year - 1), "anterior2": cols.get(year - 2)}


def parse_ingresos(year: int) -> dict:
    ws = load_sheet(find_file(year, "A2"), str(year))
    capitulos = {}
    capitulo = None
    cols = None
    for row in ws.iter_rows(values_only=True):
        row = tuple(row) + (None,) * 12
        codigo, nombre = row[1], row[2]
        if not isinstance(nombre, str):
            continue
        nombre = nombre.strip()
        clave = norm(nombre)

        def valor(campo):
            return num(row[cols[campo]]) if cols and cols[campo] is not None else None

        if m := _CABECERA.match(clave):
            n = _ROMANOS[m.group(1).upper()]
            cols = _columnas(row, year)
            corto, oficial = CAPITULOS_INGRESOS[n]
            capitulo = {"cap": n, "corto": corto, "oficial": oficial, "anterior2": None, "anterior": None, "actual": None, "conceptos": []}
            capitulos[n] = capitulo
        elif m := _TOTAL.match(clave):
            c = capitulos[_ROMANOS[m.group(1).upper()]]
            c["anterior2"], c["anterior"], c["actual"] = valor("anterior2"), valor("anterior"), valor("actual")
        elif capitulo is not None and codigo is not None and not clave.startswith("articulo"):
            if isinstance(codigo, str) and not codigo.strip()[:1].isdigit():
                continue
            capitulo["conceptos"].append(
                {
                    "codigo": code_str(codigo),
                    "nombre": sentence_case(nombre),
                    "anterior2": valor("anterior2"),
                    "anterior": valor("anterior"),
                    "actual": valor("actual"),
                }
            )
    # Si una celda de total viene rota (#REF! en el Excel de 2024), se suman los conceptos del capítulo.
    for c in capitulos.values():
        for campo in ("anterior2", "anterior", "actual"):
            if c[campo] is None and any(x[campo] is not None for x in c["conceptos"]):
                c[campo] = round(sum(x[campo] or 0 for x in c["conceptos"]), 2)
    return {"anio": year, "capitulos": [capitulos[n] for n in sorted(capitulos)]}
