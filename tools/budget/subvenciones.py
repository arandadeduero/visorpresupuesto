"""A12 · Anexo de subvenciones nominativas (y aportaciones y cuotas a asociaciones)."""
import unicodedata
from collections import Counter, defaultdict

from .common import find_file, load_sheet, norm, num, sentence_case

_MINUSCULAS = {"de", "del", "la", "las", "el", "los", "y", "e", "en", "a", "al", "con", "para", "por", "contra", "sobre"}


def _limpia(texto) -> str:
    return " ".join(str(texto).split())  # también cambia \xa0 por espacio


def _nombre(texto, entidad=False) -> str:
    """Limpia el texto; si viene todo en mayúsculas (Excel de 2024) lo pasa a minúsculas con inicial.
    Los nombres de entidad se dejan en «Título» («Cruz Roja») y los de una sola palabra, por si son siglas, tal cual."""
    t = _limpia(texto)
    if not t.isupper():
        return t
    if not entidad:
        return sentence_case(t)
    if " " not in t:
        return t
    palabras = t.lower().split(" ")
    return " ".join(p if (i and p in _MINUSCULAS) else p[:1].upper() + p[1:] for i, p in enumerate(palabras))


def _clave(nombre: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return sin_tildes.casefold()


def _es_numero(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def parse_subvenciones(year: int) -> dict:
    """Dos bloques en la misma hoja: «subvenciones nominativas» y «aportaciones y cuotas a asociaciones».

    Cada bloque tiene programas con una fila de partida (p. ej. «2311 489.00») y debajo las entidades. En «Turismo» y
    «Desarrollo económico» la fila de la partida es además la primera entidad (lleva importes) y el nombre del programa
    está en la fila de título de encima; un mismo programa puede tener varias partidas (467.00 y 489.00)."""
    ws = load_sheet(find_file(year, "A12"), str(year))
    programas = []
    prog = None
    titulo = None
    bloque = "nominativas"
    for row in ws.iter_rows(values_only=True):
        row = tuple(row) + (None,) * 8
        partida, credito, col_d, objeto = row[1], row[2], row[3], row[4]
        con_importes = _es_numero(row[5]) or _es_numero(row[6])
        texto_d = _limpia(col_d) if isinstance(col_d, str) else ""
        if norm(texto_d).startswith("aportaciones y cuotas"):
            bloque, prog, titulo = "cuotas", None, None
        elif isinstance(partida, str) and partida.strip()[:1].isdigit() and texto_d:
            codigo = partida.split()[0]
            nombre_programa = sentence_case(texto_d) if not con_importes else (titulo or sentence_case(texto_d))
            existente = next((p for p in programas if p["bloque"] == bloque and p["codigo"] == codigo), None)
            if existente is not None:  # otra partida del mismo programa (4320 467.00 y 4320 489.00)
                prog = existente
            else:
                prog = {
                    "bloque": bloque,
                    "codigo": codigo,
                    "partida": _limpia(partida),
                    "programa": nombre_programa,
                    "credito": num(credito),
                    "anterior": 0.0,
                    "actual": 0.0,
                    "items": [],
                }
                programas.append(prog)
            if con_importes:  # la fila de la partida es también una entidad
                _anade_item(prog, texto_d, objeto, row)
        elif prog is not None and partida is None and texto_d and (isinstance(objeto, str) or con_importes):
            _anade_item(prog, texto_d, objeto, row)
        elif partida is None and texto_d and not con_importes and not isinstance(objeto, str) and norm(texto_d) not in ("entidad beneficiaria", "programa"):
            titulo = sentence_case(texto_d)  # fila de título («TURISMO», «DESARROLLO ECONÓMICO»), no es una entidad

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


def _anade_item(prog, texto_d, objeto, row):
    item = {
        "entidad": _nombre(texto_d, entidad=True),
        "objeto": _nombre(objeto) if isinstance(objeto, str) else "",
        "anterior": num(row[5]) or 0.0,
        "actual": num(row[6]) or 0.0,
    }
    prog["items"].append(item)
    prog["anterior"] = round(prog["anterior"] + item["anterior"], 2)
    prog["actual"] = round(prog["actual"] + item["actual"], 2)
