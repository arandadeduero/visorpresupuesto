"""A1 · Resumen por capítulos."""
from .common import find_file, largest_remainder, load_sheet, num
from .labels import BLOQUES_100, CAPITULOS_GASTOS, CAPITULOS_INGRESOS, POBLACION


def _capitulos(rows, etiquetas):
    caps = []
    for row in rows:
        cap, actual, anterior = row[1], num(row[3]), num(row[4])
        if isinstance(cap, (int, float)) and not isinstance(cap, bool) and 1 <= cap <= 9:
            corto, oficial = etiquetas[int(cap)]
            caps.append({"cap": int(cap), "corto": corto, "oficial": oficial, "anterior": anterior, "actual": actual})
    return caps


def parse_resumen(year: int) -> dict:
    ws = load_sheet(find_file(year, "A1"), str(year))
    rows = [tuple(r) for r in ws.iter_rows(values_only=True)]
    rows = [r + (None,) * (6 - len(r)) for r in rows]

    corte = next(i for i, r in enumerate(rows) if r[1] == "ESTADO DE INGRESOS")
    gastos = _capitulos(rows[:corte], CAPITULOS_GASTOS)
    ingresos = _capitulos(rows[corte:], CAPITULOS_INGRESOS)

    def total(rows_, etiqueta):
        r = next(r for r in rows_ if r[1] == etiqueta)
        return num(r[3]), num(r[4])

    total_gastos, total_gastos_2025 = total(rows[:corte], "TOTAL GASTOS")
    total_ingresos, _ = total(rows[corte:], "TOTAL INGRESOS")

    por_cap = {c["cap"]: c["actual"] for c in gastos}
    importes = [sum(por_cap[c] for c in caps) for _, caps in BLOQUES_100]
    euros = largest_remainder(importes)
    por100 = [
        {"bloque": nombre, "caps": caps, "importe": round(imp, 2), "euros": e}
        for (nombre, caps), imp, e in zip(BLOQUES_100, importes, euros)
    ]

    habitantes, anio_poblacion, fuente = POBLACION[year]
    return {
        "anio": year,
        "tipo": "inicial",
        "habitantes": habitantes,
        "anioPoblacion": anio_poblacion,
        "fuentePoblacion": fuente,
        "totalGastos": total_gastos,
        "totalGastosAnterior": total_gastos_2025,
        "totalIngresos": total_ingresos,
        "gastosPorCapitulo": gastos,
        "ingresosPorCapitulo": ingresos,
        "por100": por100,
    }
