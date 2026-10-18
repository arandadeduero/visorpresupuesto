"""Convierte los Excel de <año>/ en JSON para la web.

Uso: python tools/convert.py 2026 [carpeta_salida]   (por defecto site/data)
"""
import json
import sys
from pathlib import Path

from budget.deuda import parse_deuda
from budget.gastos import parse_gastos
from budget.ingresos import parse_ingresos
from budget.inversiones import parse_inversiones
from budget.resumen import parse_resumen
from budget.subvenciones import parse_subvenciones

ROOT = Path(__file__).resolve().parents[1]
PARSERS = {
    "resumen": parse_resumen,
    "ingresos": parse_ingresos,
    "gastos": parse_gastos,
    "inversiones": parse_inversiones,
    "subvenciones": parse_subvenciones,
    "deuda": parse_deuda,
}
TOLERANCIA = 1.0


def _cmp(avisos, etiqueta, valor, referencia):
    if valor is None or referencia is None or abs(valor - referencia) > TOLERANCIA:
        avisos.append(f"{etiqueta}: {valor} no cuadra con {referencia}")


def check_totals(data: dict) -> list[str]:
    """Avisos si los totales de A2, A3 o A9 no cuadran con el resumen (A1)."""
    avisos = []
    res = data["resumen"]
    for nombre, clave in (("gastos", "gastosPorCapitulo"), ("ingresos", "ingresosPorCapitulo")):
        ref = {c["cap"]: c["y2026"] for c in res[clave]}
        for c in data[nombre]["capitulos"]:
            _cmp(avisos, f"{nombre}, capítulo {c['cap']}", c["y2026"], ref.get(c["cap"]))
    _cmp(avisos, "inversiones (total)", data["inversiones"]["total"], next(c["y2026"] for c in res["gastosPorCapitulo"] if c["cap"] == 6))
    return avisos


def convert(year: int, out_dir: Path) -> list[str]:
    out_dir = Path(out_dir)
    data = {nombre: parser(year) for nombre, parser in PARSERS.items()}
    destino = out_dir / str(year)
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, contenido in data.items():
        (destino / f"{nombre}.json").write_text(json.dumps(contenido, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    indice_path = out_dir / "index.json"
    anios = json.loads(indice_path.read_text(encoding="utf-8"))["anios"] if indice_path.exists() else []
    anios = sorted([a for a in anios if a["anio"] != year] + [{"anio": year, "tipo": data["resumen"]["tipo"]}], key=lambda a: a["anio"])
    indice_path.write_text(
        json.dumps({"anios": anios, "ultimo": anios[-1]["anio"]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    return check_totals(data)


if __name__ == "__main__":
    anio = int(sys.argv[1])
    salida = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "site" / "data"
    for aviso in convert(anio, salida):
        print("AVISO:", aviso)
    print(f"Datos de {anio} escritos en {salida}")
