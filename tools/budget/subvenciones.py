"""A12 · Anexo de subvenciones nominativas."""
import unicodedata
from collections import Counter, defaultdict

from .common import find_file, load_sheet, num, sentence_case


def _limpia(texto) -> str:
    return " ".join(str(texto).split())  # también cambia \xa0 por espacio


def _clave(nombre: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return sin_tildes.casefold()


def parse_subvenciones(year: int) -> dict:
    ws = load_sheet(find_file(year, "A12"), str(year))
    programas = []
    prog = None
    for row in ws.iter_rows(values_only=True):
        row = tuple(row) + (None,) * (8 - len(row))
        partida, credito, col_d = row[1], row[2], row[3]
        if isinstance(partida, str) and partida.strip()[:1].isdigit() and isinstance(col_d, str):
            prog = {
                "partida": _limpia(partida),
                "programa": sentence_case(_limpia(col_d)),
                "credito": num(credito),
                "anterior": 0.0,
                "actual": 0.0,
                "items": [],
            }
            programas.append(prog)
        elif prog is not None and isinstance(col_d, str) and col_d.strip():
            item = {
                "entidad": _limpia(col_d),
                "objeto": _limpia(row[4]) if isinstance(row[4], str) else "",
                "anterior": num(row[5]) or 0.0,
                "actual": num(row[6]) or 0.0,
            }
            prog["items"].append(item)
            prog["anterior"] = round(prog["anterior"] + item["anterior"], 2)
            prog["actual"] = round(prog["actual"] + item["actual"], 2)

    por_entidad = defaultdict(lambda: {"nombres": Counter(), "anterior": 0.0, "actual": 0.0, "programas": []})
    for p in programas:
        for it in p["items"]:
            e = por_entidad[_clave(it["entidad"])]
            e["nombres"][it["entidad"]] += 1
            e["anterior"] += it["anterior"]
            e["actual"] += it["actual"]
            if p["programa"] not in e["programas"]:
                e["programas"].append(p["programa"])
    entidades = sorted(
        (
            {
                "entidad": e["nombres"].most_common(1)[0][0],
                "anterior": round(e["anterior"], 2),
                "actual": round(e["actual"], 2),
                "programas": e["programas"],
            }
            for e in por_entidad.values()
        ),
        key=lambda e: -e["actual"],
    )
    return {
        "anio": year,
        "totalAnterior": round(sum(p["anterior"] for p in programas), 2),
        "total": round(sum(p["actual"] for p in programas), 2),
        "programas": [p for p in programas if p["items"]],
        "entidades": entidades,
    }
