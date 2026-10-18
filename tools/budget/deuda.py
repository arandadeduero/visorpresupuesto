"""A13.1 · Estado de la deuda y A13.2 · Carga financiera."""
from datetime import date, datetime

from .common import find_file, load_sheet, num

# Posición (0-based) de cada columna en la hoja AMORTIZACIONES.
_FECHA, _ENTIDAD, _IMPORTE, _PRIMERA, _ULTIMA, _TIPO = 1, 2, 3, 4, 5, 6
_VIVA_2023_01_01, _VIVA_2023_12_31, _VIVA_2024_12_31, _VIVA_2025_12_31 = 9, 11, 14, 17
_VIVA_INICIO, _AMORT, _VIVA_FIN = 18, 19, 20


def _iso(v) -> str | None:
    return v.strftime("%Y-%m-%d") if isinstance(v, (datetime, date)) else None


def project_balance(viva_base: float, amortizacion_anual: float, anio_base: int, ultima: date, anio: int) -> float:
    """Saldo a 31/12/`anio` con cuota anual constante; 0 desde el año de la última amortización."""
    if anio >= ultima.year:
        return 0.0
    return round(max(0.0, viva_base - amortizacion_anual * (anio - anio_base)), 2)


def _carga(year: int) -> dict:
    ws = load_sheet(find_file(year, "A13.2"), "Hoja1")
    intereses, amortizaciones = [], []
    for row in ws.iter_rows(values_only=True):
        row = tuple(row) + (None,) * 7
        etiqueta = row[5]
        if isinstance(etiqueta, str):
            if etiqueta.startswith("TOTAL INTERESES"):
                intereses.append(num(row[6]))
            elif "TOTAL" in etiqueta and "AMORTIZACI" in etiqueta:
                amortizaciones.append(num(row[6]))
    return {
        "intereses": intereses[0],
        "amortizacion": amortizaciones[0],
        "total": round(intereses[0] + amortizaciones[0], 2),
        "interesesConPrevisto": intereses[1],
    }


def parse_deuda(year: int) -> dict:
    ws = load_sheet(find_file(year, "A13.1"), "AMORTIZACIONES")
    prestamos, previsto = [], None
    for row in ws.iter_rows(values_only=True):
        row = tuple(row) + (None,) * 21
        if not isinstance(row[_FECHA], datetime):
            continue
        if row[_ENTIDAD] is not None and row[_ENTIDAD].strip("* ") and num(row[_VIVA_INICIO]) is not None:
            prestamos.append(
                {
                    "fecha": _iso(row[_FECHA]),
                    "entidad": row[_ENTIDAD].strip(),
                    "importe": num(row[_IMPORTE]),
                    "primeraAmortizacion": _iso(row[_PRIMERA]),
                    "ultimaAmortizacion": _iso(row[_ULTIMA]),
                    "tipoInteres": row[_TIPO].strip(),
                    "vivaInicio": num(row[_VIVA_INICIO]),
                    "vivaFin": num(row[_VIVA_FIN]),
                    "amortizacion": num(row[_AMORT]),
                    "_hist": [num(row[c]) for c in (_VIVA_2023_01_01, _VIVA_2023_12_31, _VIVA_2024_12_31, _VIVA_2025_12_31)],
                }
            )
        else:  # fila sin saldos históricos: préstamo previsto (entidad «******»)
            previsto = {
                "fecha": _iso(row[_FECHA]),
                "importe": num(row[_IMPORTE]),
                "primeraAmortizacion": _iso(row[_PRIMERA]),
                "ultimaAmortizacion": _iso(row[_ULTIMA]),
                "tipoInteres": row[_TIPO].strip().capitalize(),
            }

    serie = {2022 + i: round(sum(p["_hist"][i] for p in prestamos), 2) for i in range(4)}
    serie[2026] = round(sum(p["vivaFin"] for p in prestamos), 2)
    anio = 2026
    while serie[anio] > 0:
        anio += 1
        serie[anio] = round(
            sum(
                project_balance(p["vivaFin"], p["amortizacion"], 2026, date.fromisoformat(p["ultimaAmortizacion"]), anio)
                for p in prestamos
            ),
            2,
        )
    for p in prestamos:
        del p["_hist"]
    return {
        "anio": year,
        "prestamos": prestamos,
        "previsto": previsto,
        "serie": [{"anio": a, "viva": v} for a, v in sorted(serie.items())],
        "titular": {
            "vivaFin": serie[2026],
            "vivaFinConPrevisto": round(serie[2026] + previsto["importe"], 2),
        },
        "carga": _carga(year),
    }
