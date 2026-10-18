"""Utilidades de lectura de los Excel del presupuesto."""
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]


def SRC_DIR(year: int) -> Path:
    return ROOT / str(year)


def find_file(year: int, prefix: str) -> Path:
    """Único fichero .xlsx de la carpeta del año cuyo nombre empieza por `prefix` + espacio."""
    matches = [
        p
        for p in sorted(SRC_DIR(year).glob("*.xlsx"))
        if p.name.startswith(prefix + " ") and not p.name.startswith("~$")
    ]
    if len(matches) != 1:
        raise FileNotFoundError(f"Se esperaba un único fichero {prefix} en {SRC_DIR(year)}, hay {len(matches)}")
    return matches[0]


def load_sheet(path: Path, sheet: str):
    wb = openpyxl.load_workbook(path, data_only=True)
    return wb[sheet]


def num(v):
    """Número redondeado a 2 decimales, o None si la celda no es numérica."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return round(float(v), 2)


def code_str(v):
    if v is None:
        return None
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, int):
        return str(v)
    return str(v).strip()


_SIGLAS = {"IVA", "ARU", "ORA", "IBI", "ICIO", "IAE", "IVTM", "UNED", "FEMP", "EDAR", "PRTR"}


def sentence_case(text: str) -> str:
    """«IMPUESTO SOBRE EL IVA» → «Impuesto sobre el IVA». Respeta los textos que ya están en minúsculas
    y las palabras que ya llevan minúsculas (p. ej. «(Ley 7/2022)») dentro de un texto en mayúsculas."""
    text = " ".join(text.split())
    letras = [c for c in text if c.isalpha()]
    if not letras or sum(c.isupper() for c in letras) / len(letras) < 0.6:
        return text
    out = []
    for w in text.split(" "):
        core = re.sub(r"[^\wÁÉÍÓÚÑ]", "", w)
        conserva = any(c.islower() for c in w) or core in _SIGLAS
        out.append(w if conserva else w.lower())
    out[0] = out[0][:1].upper() + out[0][1:]
    return " ".join(out)


def largest_remainder(values: list[float], total: int = 100) -> list[int]:
    """Redondea a enteros de forma que sumen exactamente `total` (método del resto mayor)."""
    s = sum(values)
    scaled = [v * total / s for v in values]
    floors = [int(x) for x in scaled]
    missing = total - sum(floors)
    order = sorted(range(len(values)), key=lambda i: scaled[i] - floors[i], reverse=True)
    for i in order[:missing]:
        floors[i] += 1
    return floors
