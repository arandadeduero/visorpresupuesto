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


# Diferencias que ya vienen en el propio Excel oficial y que no son un fallo del conversor: año → (ingresos − gastos, explicación).
DESCUADRES_CONOCIDOS = {
    2025: (
        250000.0,
        "En el Excel de 2025 el total de ingresos (65.078.315,20 €) supera en 250.000 € al de gastos (64.828.315,20 €); "
        "el propio fichero lo marca como «Diff total» en A1. El presupuesto de 2026 recoge para 2025 un capítulo 2 de gastos "
        "con 250.000 € más (19.680.030 € en lugar de 19.430.030 €).",
    ),
}


def check_totals(data: dict, year: int | None = None) -> list[str]:
    """Avisos si los totales de A2, A3, A9 o A13 no cuadran entre sí o con el resumen (A1)."""
    avisos = []
    res = data["resumen"]
    esperado = DESCUADRES_CONOCIDOS.get(year, (0.0, ""))[0]
    _cmp(avisos, "ingresos y gastos totales (ingresos − gastos)", res["totalIngresos"] - res["totalGastos"], esperado)
    for nombre, clave in (("gastos", "gastosPorCapitulo"), ("ingresos", "ingresosPorCapitulo")):
        ref = {c["cap"]: c["actual"] for c in res[clave]}
        for c in data[nombre]["capitulos"]:
            _cmp(avisos, f"{nombre}, capítulo {c['cap']}", c["actual"], ref.get(c["cap"]))
    for c in data["gastos"]["capitulos"]:
        suma = sum(p["actual"] or 0 for p in data["gastos"]["partidas"] if p["cap"] == c["cap"])
        _cmp(avisos, f"gastos, capítulo {c['cap']}: las partidas suman {round(suma, 2)} y el capítulo", suma, c["actual"])
    for c in data["ingresos"]["capitulos"]:
        suma = sum(x["actual"] or 0 for x in c["conceptos"])
        _cmp(avisos, f"ingresos, capítulo {c['cap']}: los conceptos suman {round(suma, 2)} y el capítulo", suma, c["actual"])
    suma_proyectos = sum(pr["importe"] for p in data["inversiones"]["programas"] for pr in p["proyectos"])
    _cmp(avisos, f"inversiones: los proyectos suman {round(suma_proyectos, 2)} y el total", suma_proyectos, data["inversiones"]["total"])
    _cmp(avisos, "inversiones (total)", data["inversiones"]["total"], next(c["actual"] for c in res["gastosPorCapitulo"] if c["cap"] == 6))
    deuda = data["deuda"]
    suma_amortizacion = sum(p["amortizacion"] for p in deuda["prestamos"])
    _cmp(avisos, f"deuda: la amortización de los préstamos suma {round(suma_amortizacion, 2)} y la de la carga financiera", suma_amortizacion, deuda["carga"]["amortizacion"])
    return avisos


def notas_conocidas(data: dict, year: int) -> list[str]:
    """Explicaciones de diferencias esperadas del Excel de ese año (no son avisos)."""
    if year in DESCUADRES_CONOCIDOS:
        res = data["resumen"]
        if abs(res["totalIngresos"] - res["totalGastos"] - DESCUADRES_CONOCIDOS[year][0]) <= TOLERANCIA:
            return [DESCUADRES_CONOCIDOS[year][1]]
    return []


def convert(year: int, out_dir: Path) -> list[str]:
    """Escribe los JSON del año y devuelve los avisos (lista vacía si todo cuadra)."""
    return convert_con_notas(year, out_dir)[0]


def convert_con_notas(year: int, out_dir: Path) -> tuple[list[str], list[str]]:
    out_dir = Path(out_dir)
    data = {nombre: parser(year) for nombre, parser in PARSERS.items()}
    notas = notas_conocidas(data, year)
    if notas:
        data["resumen"]["notas"] = notas  # la web las enseña tal cual en el resumen
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
    return check_totals(data, year), notas


if __name__ == "__main__":
    anio = int(sys.argv[1])
    salida = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "site" / "data"
    avisos, notas = convert_con_notas(anio, salida)
    for aviso in avisos:
        print("AVISO:", aviso)
    for nota in notas:
        print("NOTA:", nota)
    print(f"Datos de {anio} escritos en {salida}")
