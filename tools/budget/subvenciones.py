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
    actual = None
    for row in ws.iter_rows(values_only=True):
        row = tuple(row) + (None,) * (8 - len(row))
        partida, credito, col_d = row[1], row[2], row[3]
        if isinstance(partida, str) and partida.strip()[:1].isdigit() and isinstance(col_d, str):
            actual = {
                "partida": _limpia(partida),
                "programa": sentence_case(_limpia(col_d)),
                "credito": num(credito),
                "total2025": 0.0,
                "total2026": 0.0,
                "items": [],
            }
            programas.append(actual)
        elif actual is not None and isinstance(col_d, str) and col_d.strip():
            item = {
                "entidad": _limpia(col_d),
                "objeto": _limpia(row[4]) if isinstance(row[4], str) else "",
                "y2025": num(row[5]) or 0.0,
                "y2026": num(row[6]) or 0.0,
            }
            actual["items"].append(item)
            actual["total2025"] = round(actual["total2025"] + item["y2025"], 2)
            actual["total2026"] = round(actual["total2026"] + item["y2026"], 2)

    por_entidad = defaultdict(lambda: {"nombres": Counter(), "total2025": 0.0, "total2026": 0.0, "programas": []})
    for p in programas:
        for it in p["items"]:
            e = por_entidad[_clave(it["entidad"])]
            e["nombres"][it["entidad"]] += 1
            e["total2025"] += it["y2025"]
            e["total2026"] += it["y2026"]
            if p["programa"] not in e["programas"]:
                e["programas"].append(p["programa"])
    entidades = sorted(
        (
            {
                "entidad": e["nombres"].most_common(1)[0][0],
                "total2025": round(e["total2025"], 2),
                "total2026": round(e["total2026"], 2),
                "programas": e["programas"],
            }
            for e in por_entidad.values()
        ),
        key=lambda e: -e["total2026"],
    )
    return {
        "anio": year,
        "total2025": round(sum(p["total2025"] for p in programas), 2),
        "total2026": round(sum(p["total2026"] for p in programas), 2),
        "programas": [p for p in programas if p["items"]],
        "entidades": entidades,
    }
