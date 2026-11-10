"""Extrae del PDF del presupuesto 2022 los Excel de anexos (A1, A2, A3, A9, A12, A13.1, A13.2) con el formato
que esperan los parsers de tools/budget/.

Uso: python extraer_2022.py <texto pdftotext -layout> <carpeta salida>
"""
import re
import sys
from datetime import datetime
from pathlib import Path

import openpyxl

TXT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
PAGES = TXT.read_text().split("\f")
YEAR = 2022
AMT_RE = r"-?[\d.]+,\d\d"
AMT = rf"({AMT_RE}) ?€?"
ROM = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9}


def n(s: str) -> float:
    return float(s.replace(".", "").replace(",", "."))


def page(p: int) -> list[str]:
    return PAGES[p - 1].splitlines()


def save(nombre: str, hoja: str, filas: list[list]):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = hoja
    for f in filas:
        ws.append(f)
    wb.save(OUT / nombre)


def check(cond, msg):
    if not cond:
        raise SystemExit("ERROR: " + msg)


# ---------- A1 (p. 2): resumen por capítulos, 2022 y 2021 ----------
def a1():
    filas = [[None, f"PRESUPUESTO GENERAL AYUNTAMIENTO {YEAR}"], [None, "ESTADO DE GASTOS"],
             [None, "CAP. ", "DESCRIPCIÓN", f"CRÉDITOS {YEAR}", f"CRÉDITOS {YEAR - 1}"]]
    caps = {"g": {}, "i": {}}
    totales = {}
    lado = "g"
    for l in page(2):
        s = l.strip()
        if s.startswith("ESTADO DE INGRESOS"):
            lado = "i"
            filas += [[], [None, "ESTADO DE INGRESOS"], [None, "CAP. ", "DESCRIPCIÓN", f"PREVISIONES {YEAR}", f"PREVISIONES {YEAR - 1}"]]
        elif m := re.fullmatch(rf"(\d)\s+(.+?)\s+{AMT}\s+{AMT}\s+.*", s):
            caps[lado][int(m[1])] = (n(m[3]), n(m[4]))
            filas.append([None, int(m[1]), m[2], n(m[3]), n(m[4])])
        elif m := re.fullmatch(rf"(TOTAL (?:GASTOS|INGRESOS|OP\. NO FINANCIERAS|OP\. FINANCIERAS))\s+{AMT}\s+{AMT}\s+.*", s):
            if m[1] in ("TOTAL GASTOS", "TOTAL INGRESOS"):
                totales[m[1]] = (n(m[2]), n(m[3]))
                filas.append([None, m[1], None, n(m[2]), n(m[3])])
            else:
                filas.append([None, None, m[1], n(m[2]), n(m[3])])
    for lado, tot in (("g", "TOTAL GASTOS"), ("i", "TOTAL INGRESOS")):
        check(len(caps[lado]) == 9, f"A1 {lado}: {len(caps[lado])} capítulos")
        for k in (0, 1):
            check(abs(sum(v[k] for v in caps[lado].values()) - totales[tot][k]) < 0.01, f"A1 {tot} columna {k}")
    save(f"A1 RESUMEN POR CAPITULOS {YEAR}.xlsx", str(YEAR), filas)
    return caps


# ---------- A2 (p. 3-6): estado de ingresos, solo 2022 ----------
def a2(caps_a1):
    filas = []
    cap = None
    conceptos = {}
    articulos = {}
    for p in range(3, 7):
        for l in page(p):
            s = l.strip()
            if m := re.fullmatch(r"CAPÍTULO ([IVX]+): (.+?)\s+PREVISIONES", s):
                rom, nombre = m[1], m[2]
                if cap == ROM[rom]:  # errata del PDF (p. 6): el capítulo IX viene rotulado «CAPÍTULO VIII: ACTIVOS FINANCIEROS»
                    rom, nombre = "IX", "PASIVOS FINANCIEROS"
                cap = ROM[rom]
                conceptos[cap] = []
                filas += [[], [None, "CLASIFIC. ECONÓMICA", f"CAPÍTULO {rom}: {nombre}", f"AÑO {YEAR}"]]
            elif m := re.fullmatch(rf"(\d{{3}}(?:\.\d\d)?)\s+(.+?)\s+{AMT}", s):
                conceptos[cap].append(n(m[3]))
                filas.append([None, m[1], m[2], n(m[3])])
            elif m := re.fullmatch(rf"ARTÍCULO (\d\d)\s+{AMT}", s):
                articulos[m[1]] = n(m[2])
                filas.append([None, None, f"ARTÍCULO {m[1]}", n(m[2])])
            elif m := re.fullmatch(rf"TOTAL CAPÍTULO ([IVX]+)\s+{AMT}", s):
                check(ROM[m[1]] == cap, f"A2 total {m[1]} fuera de sitio")
                tot = n(m[2])
                check(abs(sum(conceptos[cap]) - tot) < 0.01, f"A2 capítulo {cap}: conceptos {sum(conceptos[cap])} != {tot}")
                check(abs(tot - caps_a1["i"][cap][0]) < 0.01, f"A2 capítulo {cap} != A1")
                filas.append([None, None, f"TOTAL CAPÍTULO {m[1]}", tot])
            elif re.search(AMT_RE, s) and "PREVISIONES TOTALES" not in s:
                raise SystemExit(f"A2 línea sin clasificar (p. {p}): {l!r}")
    save(f"A2 ESTADO DE INGRESOS {YEAR}.xlsx", str(YEAR), filas)
    return sum(len(v) for v in conceptos.values())


# ---------- A3 (p. 8-48): estado de gastos, solo 2022 ----------
def a3(caps_a1):
    filas = []
    cap = None
    prog = None
    por_prog = {}
    por_cap = {}
    npartidas = 0
    for p in range(8, 49):
        for l in page(p):
            s = l.strip()
            if not s or s in ("ESTADO DE GASTOS", "CRÉDITOS", str(YEAR)) or re.fullmatch(r"CLASIFICACIÓN(\s+CRÉDITOS)?", s):
                continue
            if m := re.search(r"\bCAPITULO ([IVX]+)\b", s):
                cap = ROM[m[1]]
                por_cap[cap] = 0.0
                filas += [[], [None, "CLASIFICACIÓN", None, f"CAPITULO {m[1]}"], [None, "PROGRAMA", "ECONÓMICA"]]
            elif re.fullmatch(rf"PROGRAMA\s+ECONÓMICA\s+{YEAR}", s):
                continue
            elif m := re.fullmatch(rf"TOTAL CAPÍTULO ([IVX]+)\s+{AMT}", s):
                tot = n(m[2])
                check(ROM[m[1]] == cap, "A3 total fuera de sitio")
                check(abs(por_cap[cap] - tot) < 0.01, f"A3 capítulo {cap}: partidas {por_cap[cap]} != {tot}")
                check(abs(tot - caps_a1["g"][cap][0]) < 0.01, f"A3 capítulo {cap} != A1")
                filas += [[], [None, None, None, f"TOTAL CAPÍTULO {m[1]}", None, None, tot]]
            elif m := re.fullmatch(rf"TOTAL ESTADO DE GASTOS\s+{AMT}", s):
                filas.append([None, None, None, "TOTAL ESTADO DE GASTOS", None, None, n(m[1])])
            elif m := re.fullmatch(r"(\d{4})\s+([^\d\s].*)", s):
                prog = m[1]
                por_prog[prog] = 0.0
                filas += [[], [None, prog, None, m[2], None, YEAR - 1, YEAR]]
            elif m := re.fullmatch(rf"(\d{{3}}(?:\.\d\d)?)\s+(\S.*?)\s+{AMT}", s):
                v = n(m[3])
                por_prog[prog] += v
                por_cap[cap] += v
                npartidas += 1
                filas.append([None, None, m[1], m[2], None, None, v])
            elif m := re.fullmatch(rf"(?:(\d{{4}})\s+)?{AMT}", s):  # subtotal del programa (en 1510 del cap. VI sin código)
                check(abs(por_prog[prog] - n(m[2])) < 0.01, f"A3 subtotal {s!r} != {por_prog[prog]}")
                if m[1] not in (None, prog):  # errata en el rótulo del subtotal: el importe sí cuadra
                    print(f"NOTA A3 p. {p}: el subtotal de {prog} viene rotulado {m[1]}")
            else:
                raise SystemExit(f"A3 línea sin clasificar (p. {p}): {l!r}")
    check(set(por_cap) == {c for c, v in caps_a1["g"].items() if v[0]}, "A3 faltan capítulos")
    save(f"A3 ESTADO DE GASTOS {YEAR}.xlsx", str(YEAR), filas)
    return npartidas


# ---------- A9 (p. 127-129): anexo de inversiones ----------
COLS9 = ["importe", "prestamo", "corrientes", "enajen", "subvenc", "total"]


def a9(caps_a1):
    filas = [[f"ANEXO INVERSIONES REALES {YEAR}"], [],
             ["PARTIDA/CÓDIGO", "PROYECTO", "IMPORTE", "PRÉSTAMO", "INGRESOS CORRIENTES", "OTROS (ENAJENACIÓN DE INVERSIONES)",
              "REMANENTE DE TESORERÍA AFECTADO (CAP 8)", "SUBVENC.", "TOTAL"], []]
    proyectos = []
    total_pdf = None
    for p in range(127, 130):
        lineas = page(p)
        # Fin de cada columna según los rótulos de la cabecera (los importes van alineados a la derecha)
        h = next(l for l in lineas if "PROYECTO" in l and "IMPORTE" in l)
        h3 = next(l for l in lineas if "CORRIENTES" in l)
        fin = {"importe": h.index("IMPORTE") + 7, "prestamo": h.index("PRÉSTAMO") + 8, "corrientes": h3.index("CORRIENTES") + 10,
               "enajen": h3.index("INVERSIONES") + 11, "subvenc": h.index("SUBVENC.") + 8, "total": h.rindex("TOTAL") + 5}

        def importes(l):
            vals = {c: 0.0 for c in COLS9}
            for m in re.finditer(AMT, l):
                col = min(COLS9, key=lambda c: abs(fin[c] - m.end()))
                check(vals[col] == 0.0 or n(m[1]) == 0.0, f"A9 dos importes en {col}: {l!r}")
                vals[col] += n(m[1])
            return vals

        for l in lineas:
            s = l.strip()
            if "PROYECTOS PLURIANUALES" in s:
                break
            if m := re.fullmatch(r"(\d{4}) ([^\d\s].+)", s):
                filas += [[], [m[1], m[2]]]
            elif m := re.fullmatch(r"(\d{3}) ([^\d\s].+)", s):
                filas.append([m[1], m[2]])
            elif m := re.fullmatch(rf"(\d{{3}}/\d{{4}}) (.+?)\s+{AMT}.*", s):
                v = importes(l)
                check(abs(v["importe"] - v["total"]) < 0.01 and abs(sum(v[c] for c in COLS9[1:5]) - v["importe"]) < 0.01, f"A9 financiación {s!r} {v}")
                proyectos.append(v)
                filas.append([m[1], m[2], v["importe"], v["prestamo"], v["corrientes"], v["enajen"], 0.0, v["subvenc"], v["total"]])
            elif s.startswith("TOTAL CAPITULO VI"):
                v = importes(l)
                total_pdf = v
                filas += [[], [None, "TOTAL CAPITULO VI", v["importe"], v["prestamo"], v["corrientes"], v["enajen"], 0.0, v["subvenc"], v["total"]]]
    for c in COLS9:
        suma = round(sum(x[c] for x in proyectos), 2)
        check(abs(suma - total_pdf[c]) < 0.01, f"A9 columna {c}: proyectos {suma} != total {total_pdf[c]}")
    check(abs(total_pdf["total"] - caps_a1["g"][6][0]) < 0.01, "A9 total != capítulo 6")
    save(f"A9 ANEXO DE INVERSIONES {YEAR}.xlsx", str(YEAR), filas)
    return len(proyectos), total_pdf


# ---------- A12 (p. 135-137): subvenciones nominativas y cuotas, solo 2022 ----------
def a12():
    filas = [[], [None, None, None, "SUBVENCIONES NOMINATIVAS"], [],
             [None, "PARTIDA", "CRÉDITO PARTIDA", "PROGRAMA", "OBJETO DEL CONVENIO", str(YEAR)], [None, None, None, "ENTIDAD BENEFICIARIA"]]
    totales = {"nominativas": 0.0, "cuotas": 0.0}
    bloque = "nominativas"
    total_pdf = None
    items = 0
    for p in range(135, 138):
        for l in page(p):
            s = l.strip()
            if not s or s.startswith(("CRÉDITO", "PARTIDA ", "ENTIDAD BENEFICIARIA", "ANEXO SUBVENCIONES", "SUBVENCIONES NOMINATIVAS")) or s == "PARTIDA":
                continue
            if s.startswith("APORTACIONES Y CUOTAS"):
                bloque = "cuotas"
                filas += [[], [None, None, None, "APORTACIONES Y CUOTAS ASOCIACIONES"], [],
                          [None, "PARTIDA", "CRÉDITO PARTIDA", "PROGRAMA", "CONCEPTO", str(YEAR)], [None, None, None, "ENTIDAD BENEFICIARIA"]]
            elif m := re.fullmatch(rf"TOTAL SUBVENCIONES NOMINATIVAS\s+{AMT}", s):
                total_pdf = n(m[1])
            elif m := re.fullmatch(rf"(\d{{4}} \d{{3}}\.\d\d)\s+({AMT_RE})\s+(.+)", s):
                filas += [[], [None, m[1], n(m[2]), m[3]]]
            elif m := re.fullmatch(rf"(\d{{4}})\s+{AMT}", s):  # subtotal del programa
                continue
            elif m := re.fullmatch(rf"(.+?)\s+{AMT}", s):
                partes = re.split(r"\s{2,}", m[1])
                entidad, objeto = partes[0], " ".join(partes[1:]) or None
                v = n(m[2])
                totales[bloque] += v
                items += 1
                filas.append([None, None, None, entidad, objeto, v])
            elif not re.search(r"\d", s):  # continuación del objeto («ALMACEN€»)
                filas[-1][4] = f"{filas[-1][4]} {s.rstrip('€').strip()}"
            else:
                raise SystemExit(f"A12 línea sin clasificar (p. {p}): {l!r}")
    check(abs(totales["nominativas"] - total_pdf) < 0.01, f"A12 nominativas {totales['nominativas']} != {total_pdf}")
    save(f"A12 ANEXO SUBVENCIONES NOMINATIVAS {YEAR}.xlsx", str(YEAR), filas)
    return items, totales


# ---------- A13.1 y A13.2 (p. 172-173): deuda ----------
def a13():
    d = lambda s: datetime.strptime(s, "%d/%m/%Y")
    filas = [[], [None, "ANEXO DE DEUDA"], [], [None, f"             PRÉSTAMOS A LARGO PLAZO EN VIGOR A 01/01/{YEAR}"], [],
             # El PDF rotula la deuda inicial «DEUDA VIVA 01/12/2022»: es una errata de 01/01/2022 (cuadra con la deuda a 31/12/2021)
             [None, "FECHA", "ENTIDAD", "IMPORTE", "PRIMERA AMORTIZ.", "ULTIMA AMORTIZ.", "TIPO DE INTERÉS", "AMORT.", "IMPORTE",
              f"DEUDA VIVA 01/01/{YEAR}", f"AMORTIZ. {YEAR}", f"DEUDA VIVA 31/12/{YEAR}"], []]
    tot = [0.0, 0.0, 0.0]
    total_pdf = None
    prestamos = []
    for l in page(172):
        s = l.strip()
        if m := re.fullmatch(rf"(\S+)\s+(.+?)\s+({AMT_RE})\s+(\d\d/\d\d/\d{{4}})\s+(\d\d/\d\d/\d{{4}})\s+(.+?)\s+(CTE\. (?:TRIM|ANUAL)\.?)\s+({AMT_RE})\s+({AMT_RE})\s+({AMT_RE})\s+({AMT_RE})", s):
            previsto = m[1].startswith("---")
            fila = [None, f"{YEAR} (previsto)" if previsto else d(m[1]), "PREVISTO" if previsto else m[2], n(m[3]), d(m[4]), d(m[5]), m[6], m[7], n(m[8]),
                    n(m[9]), n(m[10]), n(m[11])]
            filas += [fila, []]
            if not previsto:
                prestamos.append(m[2])
                for i in range(3):
                    tot[i] += n(m[9 + i])
        elif m := re.fullmatch(rf"({AMT_RE})\s+({AMT_RE})\s+({AMT_RE})", s):
            total_pdf = [n(m[1]), n(m[2]), n(m[3])]
    check(all(abs(a - b) < 0.01 for a, b in zip(tot, total_pdf)), f"A13.1 totales {tot} != {total_pdf}")
    check(abs(tot[0] - tot[1] + 1518595.61 - tot[2]) < 0.01, "A13.1 viva inicio − amortización + disposición Caja Laboral != viva fin")
    filas += [[None, None, None, None, None, None, None, None, None, *[round(x, 2) for x in tot]], [],
              [None, f"No hay operaciones de tesorería pendientes, ni está previsto solicitarlas en {YEAR}."]]
    save("A13.1 Estado de la deuda.xlsx", "AMORTIZACIONES", filas)

    carga = [[None, f"PREVISIÓN CARGA FINANCIERA {YEAR}"], []]
    intereses = 0.0
    for l in page(173):
        if m := re.match(rf"\s*(BANKIA|UNICAJA BANCO|CAJA LABORAL)\s.*?\s({AMT_RE})\s*(\(.*\))?$", l):
            v = n(m[2])
            intereses += v
            carga.append([None, m[1], None, None, None, f"INTERESES PRÉSTAMO {m[1]} {YEAR}", v])
    check(len(carga) == 5, "A13.2 faltan préstamos")
    carga += [[], [None, None, None, None, None, f"TOTAL INTERESES {YEAR}", round(intereses, 2)],
              [None, None, None, None, None, f"TOTAL AMORTIZACIÓN {YEAR}", round(tot[1], 2)]]
    save("A13.2 Carga Financiera.xlsx", "Hoja1", carga)
    return prestamos, tot, intereses


caps = a1()
print("A1 gastos", sum(v[0] for v in caps["g"].values()), "ingresos", sum(v[0] for v in caps["i"].values()))
print("A2 conceptos", a2(caps))
print("A3 partidas", a3(caps))
print("A9 proyectos y total", a9(caps))
print("A12 entidades y totales", a12())
print("A13 préstamos, (viva inicio, amortización, viva fin), intereses", a13())
