"""A13.1 · Estado de la deuda y A13.2 · Carga financiera."""
import re
from datetime import date, datetime

from .common import find_file, load_sheet, norm, num

_VIVA = re.compile(r"^deuda viva (\d\d)/(\d\d)/(\d{4})$")
_AMORT = re.compile(r"^amortiz\. (\d{4})$")


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
            # El año que lleva la etiqueta no es fiable (el Excel de 2025 dice «TOTAL INTERESES 2024»): se ignora.
            if etiqueta.startswith("TOTAL INTERESES"):
                intereses.append(num(row[6]))
            elif "TOTAL" in etiqueta and "AMORTIZACI" in etiqueta:
                amortizaciones.append(num(row[6]))
    return {
        "intereses": intereses[0],
        "amortizacion": amortizaciones[0],
        "total": round(intereses[0] + amortizaciones[0], 2),
        # Solo cuando el anexo incluye un préstamo previsto aparece un segundo total de intereses.
        "interesesConPrevisto": intereses[1] if len(intereses) > 1 else None,
    }


def _columnas(filas, year: int) -> dict:
    """Posición de cada columna según los rótulos de la cabecera (cambia de un ejercicio a otro)."""
    for fila in filas:
        etiquetas = [norm(v) if isinstance(v, str) else "" for v in fila]
        if "fecha" in etiquetas and "entidad" in etiquetas:
            cols = {"vivas": {}, "amort": {}}
            for i, e in enumerate(etiquetas):
                if m := _VIVA.match(e):
                    cols["vivas"][(int(m.group(3)), int(m.group(2)), int(m.group(1)))] = i  # (año, mes, día)
                elif m := _AMORT.match(e):
                    cols["amort"][int(m.group(1))] = i
                elif e in ("fecha", "entidad", "primera amortiz.", "ultima amortiz.", "tipo de interes"):
                    cols[e] = i
                elif e == "importe" and "importe" not in cols:  # la segunda «IMPORTE» es la cuota
                    cols[e] = i
            for clave in [(year, 12, 31), (year, 1, 1)]:
                if clave not in cols["vivas"]:
                    raise ValueError(f"A13.1 no tiene la columna «DEUDA VIVA {clave[2]:02d}/{clave[1]:02d}/{clave[0]}»")
            if year not in cols["amort"]:
                raise ValueError(f"A13.1 no tiene la columna «AMORTIZ. {year}»")
            return cols
    raise ValueError("No se encuentra la cabecera de A13.1")


def parse_deuda(year: int) -> dict:
    ws = load_sheet(find_file(year, "A13.1"), "AMORTIZACIONES")
    filas = [tuple(r) + (None,) * 30 for r in ws.iter_rows(values_only=True)]
    cols = _columnas(filas, year)
    vivas = cols["vivas"]
    inicio, fin, amort = vivas[(year, 1, 1)], vivas[(year, 12, 31)], cols["amort"][year]
    cierres = {y: c for (y, m, d), c in vivas.items() if (m, d) == (12, 31)}  # deuda a 31/12 de cada año del anexo
    primer_cierre = min(cierres)
    prestamos, previsto = [], None
    for row in filas:
        if not isinstance(row[cols["fecha"]], datetime):
            continue
        entidad = row[cols["entidad"]]
        base = {
            "fecha": _iso(row[cols["fecha"]]),
            "importe": num(row[cols["importe"]]),
            "primeraAmortizacion": _iso(row[cols["primera amortiz."]]),
            "ultimaAmortizacion": _iso(row[cols["ultima amortiz."]]),
        }
        tipo = row[cols["tipo de interes"]].strip()
        if isinstance(entidad, str) and entidad.strip("* "):
            prestamos.append(
                {
                    "fecha": base["fecha"],
                    "entidad": entidad.strip(),
                    "importe": base["importe"],
                    "primeraAmortizacion": base["primeraAmortizacion"],
                    "ultimaAmortizacion": base["ultimaAmortizacion"],
                    "tipoInteres": tipo,
                    "vivaInicio": num(row[inicio]),
                    "vivaFin": num(row[fin]),
                    "amortizacion": num(row[amort]),
                    "_cierres": {y: num(row[c]) for y, c in cierres.items()},
                    "_viva_1_enero_primer_anio": num(row[vivas[min(vivas)]]),
                }
            )
        else:  # fila sin entidad («******»): préstamo previsto, que no es deuda contraída
            previsto = {**base, "tipoInteres": tipo.capitalize()}

    # Deuda a final de cada año: el 01/01 del primer año del anexo equivale al cierre del año anterior.
    serie = {primer_cierre - 1: round(sum(p["_viva_1_enero_primer_anio"] for p in prestamos), 2)}
    for y in cierres:
        serie[y] = round(sum(p["_cierres"][y] for p in prestamos), 2)
    anio = year
    while serie[anio] > 0:
        anio += 1
        serie[anio] = round(
            sum(
                project_balance(p["vivaFin"], p["amortizacion"], year, date.fromisoformat(p["ultimaAmortizacion"]), anio)
                for p in prestamos
            ),
            2,
        )
    for p in prestamos:
        del p["_cierres"], p["_viva_1_enero_primer_anio"]
    return {
        "anio": year,
        "prestamos": prestamos,
        "previsto": previsto,
        "serie": [{"anio": a, "viva": v} for a, v in sorted(serie.items())],
        "titular": {
            "vivaFin": serie[year],
            # Solo si el anexo trae un préstamo previsto (el de 2024 no lo tiene).
            "vivaFinConPrevisto": round(serie[year] + previsto["importe"], 2) if previsto else None,
        },
        "carga": _carga(year),
    }
