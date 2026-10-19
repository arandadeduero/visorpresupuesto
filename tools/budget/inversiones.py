"""A9 · Anexo de inversiones reales: proyectos y su financiación."""
import re

from .common import code_str, find_file, load_sheet, norm, num, sentence_case

FUENTES = ("prestamo", "ingresosCorrientes", "otros", "rta", "subvenciones")
_COLS = {"importe": 3, "prestamo": 4, "ingresosCorrientes": 5, "otros": 6, "rta": 7, "subvenciones": 8}


def _es_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _desplazamiento(filas) -> int:
    """Columnas a añadir por la izquierda para que «PARTIDA/CÓDIGO» quede en la posición 1 (en 2024 la tabla empieza en la columna A)."""
    for fila in filas:
        for i, v in enumerate(fila[:3]):
            if isinstance(v, str) and norm(v).startswith("partida"):
                return 1 - i
    raise ValueError("No se encuentra la cabecera «PARTIDA/CÓDIGO» en A9")


def parse_inversiones(year: int) -> dict:
    ws = load_sheet(find_file(year, "A9"), str(year))
    filas = [tuple(r) for r in ws.iter_rows(values_only=True)]
    desplazamiento = _desplazamiento(filas)
    programas = []
    programa = None
    partida = None
    total = None
    fuentes = None
    for row in filas:
        row = (None,) * desplazamiento + row + (None,) * 10
        codigo, nombre = row[1], row[2]
        if isinstance(nombre, str) and norm(nombre).startswith("total capitulo vi"):
            total = num(row[9])
            fuentes = {f: num(row[_COLS[f]]) or 0.0 for f in FUENTES}
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
        elif es_texto and _es_num(row[3]) and programa is not None:  # proyecto (a veces con código propio, p. ej. «005/2023»)
            proyecto = {"nombre": nombre.strip(), "partida": partida}
            for campo, col in _COLS.items():
                proyecto[campo] = num(row[col]) or 0.0
            programa["proyectos"].append(proyecto)
            programa["total"] = round(programa["total"] + proyecto["importe"], 2)
    return {
        "anio": year,
        "total": total,
        "fuentes": fuentes,
        "programas": [p for p in programas if p["proyectos"]],
    }
