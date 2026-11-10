"""Extrae del PDF del presupuesto 2018 (texto de pdftotext -layout) los 7 Excel de anexos con el formato de 2024.

Uso: python -I extraer_2018.py <2018.txt> <carpeta_salida>
Cada bloque se comprueba contra los totales que trae el propio PDF (programa, artículo, capítulo y resumen p.4);
si algo no cuadra, el script se para con AssertionError.
"""
import re
import sys
from datetime import datetime
from pathlib import Path

import openpyxl

TXT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
PAGES = TXT.read_text(encoding="utf-8").split("\f")
YEAR = 2018
ROMANOS = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
IMP = r"-?\d{1,3}(?:\.\d{3})*,\d\d"


def eur(s):
    return round(float(s.replace(".", "").replace(",", ".")), 2)


def close(a, b):
    return abs(a - b) < 0.005


def page_lines(first, last):
    """Líneas de las páginas first..last (numeración del PDF), sin el pie «Presupuesto 2018  N»."""
    for p in range(first, last + 1):
        for line in PAGES[p - 1].splitlines():
            if re.fullmatch(r"\s*Presupuesto 2018(\s+\d+)?\s*", line) or not line.strip():
                continue
            yield p, line


def save(nombre, sheet, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    for r in rows:
        ws.append(list(r))
    wb.save(OUT / nombre)


# ---------------------------------------------------------------- A1 · resumen (p.4)
CAP_RE = re.compile(r"^CAP[ÍI]TULO ([IVX]+)\s*:\s*(.*?)\s*(?:\s(" + IMP + r") €)?\s*$")
resumen = {"gastos": {}, "ingresos": {}}
bloque = "gastos"
nombres_a1 = {"gastos": {}, "ingresos": {}}
totales_p4 = {}
for line in PAGES[3].splitlines():
    s = line.strip()
    if s == "INGRESOS":
        bloque = "ingresos"
    if m := CAP_RE.match(s):
        n = ROMANOS.index(m.group(1))
        resumen[bloque][n] = eur(m.group(3)) if m.group(3) else 0.0  # cap VI de ingresos viene sin importe
        nombres_a1[bloque][n] = m.group(2).strip()
    elif m := re.match(r"^TOTAL ESTADO DE (GASTOS|INGRESOS)\s+(" + IMP + ") €", s):
        totales_p4[m.group(1).lower()] = eur(m.group(2))
assert sorted(resumen["gastos"]) == list(range(1, 10)) and sorted(resumen["ingresos"]) == list(range(1, 10)), resumen
for b in ("gastos", "ingresos"):
    assert close(sum(resumen[b].values()), totales_p4[b]), (b, sum(resumen[b].values()), totales_p4[b])

rows = [(None,), (None, f"PRESUPUESTO GENERAL AYUNTAMIENTO {YEAR}"), (None, "ESTADO DE GASTOS"),
        (None, "CAP. ", "DESCRIPCIÓN", f"PREVISIONES {YEAR}", f"CRÉDITOS {YEAR - 1}")]
for n in range(1, 10):
    rows.append((None, n, nombres_a1["gastos"][n], resumen["gastos"][n], None))
rows.append((None, "TOTAL GASTOS", None, totales_p4["gastos"], None))
rows += [(None,), (None, "ESTADO DE INGRESOS"), (None, "CAP. ", "DESCRIPCIÓN", f"PREVISIONES {YEAR}", f"CRÉDITOS {YEAR - 1}")]
for n in range(1, 10):
    rows.append((None, n, nombres_a1["ingresos"][n], resumen["ingresos"][n], None))
rows.append((None, "TOTAL INGRESOS", None, totales_p4["ingresos"], None))
rows.append((None, f"Fuente: presupuesto municipal {YEAR} (PDF), p. 4. El PDF no trae la columna del año anterior."))
save(f"A1 RESUMEN POR CAPITULOS {YEAR}.xlsx", str(YEAR), rows)

# ---------------------------------------------------------------- A3 · gastos (p.6–68)
PROG_RE = re.compile(r"^\s*(\d{4}|0 110)(?:\s{10,}[\d.,]+)?\s*$")  # p.22: «2426   98667,84» (cifra suelta)
PARTIDA_RE = re.compile(r"^\s+(\d{2,3}(?:[.,]\d{2})?)\s+(\S.*?)\s*$")
TAIL_RE = re.compile(r"^(.*?)\s+(" + IMP + r")\s*€?\s*$")
TOTALPROG_RE = re.compile(r"^\s*TOTAL\s*(\d{4}|0 ?110)\s+(" + IMP + r")\s*€?\s*$")
TOTALCAP_RE = re.compile(r"^\s*TOTAL CAP[ÍI]TULO ([IVX]+):?\s+(" + IMP + r")")
COVER_RE = re.compile(r"^\s*CAP[ÍI]TULO ([IVX]+)\s*:?\s+(" + IMP + r") €\s*$")

rotulos_raros = []
gastos = []  # (cap, programa, nombre_programa, codigo, nombre, importe, pagina)
sin_importe = []
detalles = []
cap = prog = None
prog_nombre = []
estado = None  # "nombre" tras el código de programa; "partidas" después
ultima = None
bloque_suma = 0.0
cap_cubierta = {}
cap_total_pdf = {}
lineas_a3 = list(page_lines(6, 68))
for k, (p, line) in enumerate(lineas_a3):
    prev_line = lineas_a3[k - 1][1] if k else None
    s = line.strip()
    if m := COVER_RE.match(line):
        cap = ROMANOS.index(m.group(1))
        cap_cubierta[cap] = eur(m.group(2))
        prog = None
        continue
    if s.startswith("Clasificaci") or re.match(r"^CAP[ÍI]TULO [IVX]+\s*:", s) or re.fullmatch(r"CAP[ÍI]TULO [IVX]+", s):
        continue
    if m := TOTALCAP_RE.match(line):
        cap_total_pdf[ROMANOS.index(m.group(1))] = eur(m.group(2))
        continue
    if m := TOTALPROG_RE.match(line):
        cod = m.group(1).replace(" ", "")
        if cod != prog:
            rotulos_raros.append((p, prog, s))  # p.23: «TOTAL 2429» bajo el programa 2431 (errata del PDF)
        assert close(bloque_suma, eur(m.group(2))), (p, prog, bloque_suma, m.group(2))
        estado, ultima, bloque_suma = None, None, 0.0
        continue
    if s.startswith("TOTAL"):  # «TOTAL ÓRGANOS DE GOBIERNO» y similares (sumas de sección)
        continue
    if m := PROG_RE.match(line):
        prog = m.group(1).replace(" ", "")
        prog_nombre, estado, ultima, bloque_suma = [], "nombre", None, 0.0
        continue
    if estado == "nombre" and not PARTIDA_RE.match(line):
        prog_nombre.append(s)
        continue
    if prog is None or cap is None:
        continue  # títulos de sección del capítulo I («PERSONAL FUNCIONARIO»…)
    m = PARTIDA_RE.match(line)
    if m and len(m.group(1).split(".")[0].split(",")[0]) == 3:
        estado = "partidas"
        codigo = m.group(1).replace(",", ".")
        resto = m.group(2)
        t = TAIL_RE.match(resto)
        ultima = {"cap": cap, "programa": prog, "prog_nombre": " ".join(prog_nombre), "codigo": codigo,
                  "nombre": (t.group(1) if t else resto).strip(), "importe": eur(t.group(2)) if t else None, "pagina": p, "linea": line}
        gastos.append(ultima)
        if t:
            bloque_suma = round(bloque_suma + ultima["importe"], 2)
        continue
    if m and len(m.group(1)) == 2:  # artículo («31 Préstamos del Interior», «62 INVERSIÓN NUEVA…»)
        estado = "partidas"
        continue
    # Línea de continuación: completa la descripción de la partida anterior si aún no tenía importe
    if ultima is not None and ultima["importe"] is None:
        t = TAIL_RE.match(s)
        ultima["nombre"] += " " + (t.group(1) if t else s).strip()
        if t:
            ultima["importe"] = eur(t.group(2))
            bloque_suma = round(bloque_suma + ultima["importe"], 2)
    elif ultima is not None and ultima["linea"] == prev_line and (s[:1].islower() or s.startswith("(")):
        ultima["nombre"] += " " + s  # descripción que sigue en la línea de abajo («de lucro», «(Prevención de Riesgos Lab.)»)
    else:
        detalles.append((p, s))

sin_importe = [g for g in gastos if g["importe"] is None]
gastos = [g for g in gastos if g["importe"] is not None]
for n in range(1, 10):
    suma = round(sum(g["importe"] for g in gastos if g["cap"] == n), 2)
    assert close(suma, resumen["gastos"][n]), ("gastos cap", n, suma, resumen["gastos"][n])
    assert close(cap_cubierta[n], resumen["gastos"][n]), ("portada cap", n)
    if n in cap_total_pdf:
        assert close(cap_total_pdf[n], suma)

rows = [(None,), (None, "CLASIFICACIÓN", None, None, None, YEAR - 1, YEAR)]
for n in range(1, 10):
    rows += [(None,), (None, "CLASIFICACIÓN", None, f"CAPITULO {ROMANOS[n]}"), (None, "PROGRAMA", "ECONÓMICA", None, None, YEAR - 1, YEAR)]
    propias = [g for g in gastos if g["cap"] == n]
    i = 0
    while i < len(propias):
        prog = propias[i]["programa"]
        j = i
        while j < len(propias) and propias[j]["programa"] == prog and propias[j]["prog_nombre"] == propias[i]["prog_nombre"]:
            j += 1
        rows.append((None, prog, None, propias[i]["prog_nombre"] or f"PROGRAMA {prog}", None, YEAR - 1, YEAR))
        for g in propias[i:j]:
            rows.append((None, None, g["codigo"], g["nombre"], None, None, g["importe"]))
        rows.append((None, prog, None, None, None, None, round(sum(g["importe"] for g in propias[i:j]), 2)))
        rows.append((None,))
        i = j
    rows.append((None, None, None, f"TOTAL CAPÍTULO {ROMANOS[n]}", None, None, resumen["gastos"][n]))
rows.append((None,))
rows.append((None, f"Fuente: presupuesto municipal {YEAR} (PDF), p. 6-68. El PDF no trae la columna del año {YEAR - 1}."))
save(f"A3 ESTADO DE GASTOS {YEAR}.xlsx", str(YEAR), rows)

# ---------------------------------------------------------------- A2 · ingresos (p.70–88)
ART_RE = re.compile(r"^\s*(\d{2})\s*$")
TOTALART_RE = re.compile(r"^\s*TOTAL ART[ÍI]CULO\s+(\d{2})\s+(" + IMP + r")")
ingresos = {}  # cap → [articulos: {codigo, nombre, conceptos}]
cap = art = None
ultimo = None
art_total_pdf = []
for p, line in page_lines(70, 88):
    s = line.strip()
    if m := COVER_RE.match(line):
        cap = ROMANOS.index(m.group(1))
        ingresos[cap] = []
        art = None
        continue
    if s.startswith("Clasificaci") or re.match(r"^CAP[ÍI]TULO [IVX]+\s*:", s):
        continue
    if m := TOTALCAP_RE.match(line):
        assert close(eur(m.group(2)), resumen["ingresos"][ROMANOS.index(m.group(1))])
        continue
    if m := TOTALART_RE.match(line):
        art_total_pdf.append((p, art["codigo"], m.group(1), eur(m.group(2))))
        assert close(sum(c["importe"] for c in art["conceptos"]), eur(m.group(2))), (p, art["codigo"])
        art, ultimo = None, None
        continue
    if m := ART_RE.match(line):
        art = {"codigo": m.group(1), "nombre": [], "conceptos": []}
        ingresos[cap].append(art)
        ultimo = None
        continue
    m = PARTIDA_RE.match(line)
    if m and len(m.group(1).split(".")[0].split(",")[0]) == 3 and art is not None:
        t = TAIL_RE.match(m.group(2))
        ultimo = {"codigo": m.group(1).replace(",", "."), "nombre": (t.group(1) if t else m.group(2)).strip(), "importe": eur(t.group(2)) if t else None, "pagina": p}
        art["conceptos"].append(ultimo)
    elif art is not None and not art["conceptos"]:
        art["nombre"].append(s)
    elif ultimo is not None:  # descripción partida en dos líneas
        t = TAIL_RE.match(s)
        ultimo["nombre"] += " " + (t.group(1) if t else s).strip()
        if t:
            assert ultimo["importe"] is None, (p, s)
            ultimo["importe"] = eur(t.group(2))
    elif art is not None or len([x for x in PAGES[p - 1].splitlines() if x.strip()]) > 5:
        raise AssertionError((p, line))  # fuera de un artículo solo se admiten los títulos de las portadas
ingresos.setdefault(6, [])  # el PDF no tiene páginas del capítulo VI (0 € en el resumen)
for n in range(1, 10):
    conceptos = [c for a in ingresos[n] for c in a["conceptos"]]
    assert all(c["importe"] is not None for c in conceptos), n
    assert close(sum(c["importe"] for c in conceptos), resumen["ingresos"][n]), ("ingresos cap", n)
    assert all(c["codigo"].startswith(a["codigo"]) for a in ingresos[n] for c in a["conceptos"]), n

rows = []
for n in range(1, 10):
    rows.append((None, "CLASIFIC. ECONÓMICA", f"CAPÍTULO {ROMANOS[n]}: {nombres_a1['ingresos'][n]}", None, f"AÑO {YEAR}"))
    for a in ingresos[n]:
        for c in a["conceptos"]:
            rows.append((None, c["codigo"], c["nombre"], None, c["importe"]))
        rows.append((None, None, f"ARTÍCULO {a['codigo']}", None, round(sum(c["importe"] for c in a["conceptos"]), 2)))
    rows.append((None, None, f"TOTAL CAPÍTULO {ROMANOS[n]}", None, resumen["ingresos"][n]))
    rows += [(None,), (None,)]
rows.append((None, None, f"Fuente: presupuesto municipal {YEAR} (PDF), p. 70-88. El PDF no trae la columna del año {YEAR - 1}."))
save(f"A2 ESTADO DE INGRESOS {YEAR}.xlsx", str(YEAR), rows)

# ---------------------------------------------------------------- A9 · inversiones (p.117–121)
COLS9 = ["importe", "prestamo", "ingresosCorrientes", "otros", "subvenciones", "total"]
programas9 = []
prog = None
partida = None
total9 = None
amount_tok = re.compile(IMP + r"(?:\s*€)?")
for p in range(117, 122):
    lines = PAGES[p - 1].splitlines()
    head = next(l for l in lines if "CODIGO - PARTIDA" in l)
    labels = ["IMPORTE", "PRÉSTAMO", "ING. CORRIENTE", "CAPITULO VI", "CAPITULO VII", "TOTAL"]
    ends, pos = [], 0
    for lab in labels:
        i = head.index(lab, pos)
        ends.append(i + len(lab))
        pos = i + len(lab)
    for line in lines:
        s = line.strip()
        if not s or "CODIGO - PARTIDA" in line or s == "ENAJENACIONES" or re.fullmatch(r"Presupuesto 2018\s+\d+", s):
            continue
        if s.startswith("El Proyecto"):
            break  # cuadro de proyectos plurianuales al final de p.121
        toks = list(amount_tok.finditer(line))
        texto = line[: toks[0].start()].strip() if toks else s
        valores = {}
        for t in toks[1:]:
            end = t.start() + len(t.group().replace("€", "").rstrip())
            k = min(range(len(ends)), key=lambda i: abs(ends[i] - end))
            assert k not in valores, (p, line)
            valores[COLS9[k]] = eur(t.group().replace("€", "").strip())
        if toks:
            valores["importe"] = eur(toks[0].group().replace("€", "").strip())
        if m := re.match(r"^TOTAL\s*CAPITULO VI", texto):
            total9 = {c: valores.get(c, 0.0) for c in COLS9}
            continue
        if m := re.match(r"^TOTAL\s*(\d{4})$", texto):
            assert m.group(1) == prog["codigo"], (p, line)
            for c in COLS9:
                assert close(sum(x.get(c, 0.0) for x in prog["proyectos"]), valores.get(c, 0.0)), (p, prog["codigo"], c)
            continue
        if re.fullmatch(r"\d{4}", s):
            prog = {"codigo": s, "nombre": [], "proyectos": []}
            programas9.append(prog)
            partida = None
            continue
        if not toks and prog is not None and not prog["proyectos"] and partida is None and not re.match(r"^\d{2}\s", s):
            if not re.match(r"^\d{2}\s", s) and not line.startswith("    "):
                prog["nombre"].append(s)
                continue
        if re.match(r"^\d{2}\s", s) and not toks:
            continue  # artículo («62 INVERSIÓN NUEVA…»)
        if not toks:
            if m := re.match(r"^(\d{3})\s+(.*)$", s):
                partida = {"codigo": m.group(1), "nombre": m.group(2)}
            continue  # 2.ª línea del rótulo del artículo («OPERATIVO DE LOS SERVICIOS»)
        if m := re.match(r"^(\d{3})\s+(.*)$", texto):  # partida y proyecto en la misma línea
            partida = {"codigo": m.group(1), "nombre": m.group(2)}
            nombre = m.group(2)
        else:
            nombre = texto
        assert close(valores["importe"], valores["total"]) and close(valores["importe"], sum(valores.get(c, 0.0) for c in COLS9[1:5])), (p, line)
        prog["proyectos"].append({"partida": partida["codigo"], "partida_nombre": partida["nombre"], "nombre": nombre, **valores})

assert total9 and close(total9["total"], resumen["gastos"][6]), total9
for c in COLS9:
    assert close(sum(x.get(c, 0.0) for pr in programas9 for x in pr["proyectos"]), total9[c]), c
# Las partidas del anexo deben coincidir con las de A3 (capítulo 6), programa a programa
a3_cap6 = {}
for g in gastos:
    if g["cap"] == 6:
        a3_cap6[g["programa"]] = round(a3_cap6.get(g["programa"], 0) + g["importe"], 2)
a9 = {pr["codigo"]: round(sum(x["importe"] for x in pr["proyectos"]), 2) for pr in programas9}
assert a3_cap6 == a9, (a3_cap6, a9)

rows = [(f"ANEXO INVERSIONES REALES {YEAR}",), (None,),
        ("PARTIDA/CÓDIGO", "PROYECTO", "IMPORTE", "PRÉSTAMO", "INGRESOS CORRIENTES", "OTROS (ENAJENACIONES CAP VI)",
         "RTA (CAP 8)", "SUBVENCIONES (TRANSFERENCIAS DE CAPITAL, CAP VII)", "TOTAL"), (None,)]
for pr in programas9:
    rows.append((pr["codigo"], " ".join(pr["nombre"])))
    actual = None
    for x in pr["proyectos"]:
        if x["partida"] != actual:
            rows.append((x["partida"], x["partida_nombre"]))
            actual = x["partida"]
        rows.append((None, x["nombre"], x["importe"], x.get("prestamo"), x.get("ingresosCorrientes"), x.get("otros"), None, x.get("subvenciones"), x["total"]))
    rows.append((None, pr["codigo"], *[round(sum(x.get(c, 0.0) for x in pr["proyectos"]), 2) for c in COLS9[:4]], 0, round(sum(x.get("subvenciones", 0.0) for x in pr["proyectos"]), 2), round(sum(x["total"] for x in pr["proyectos"]), 2)))
    rows.append((None,))
rows.append((None, "TOTAL CAPITULO VI", total9["importe"], total9["prestamo"], total9["ingresosCorrientes"], total9["otros"], 0, total9["subvenciones"], total9["total"]))
rows.append((None,))
rows.append((None, f"Fuente: presupuesto municipal {YEAR} (PDF), p. 116-121. El PDF financia con préstamo, ingresos corrientes y "
             "«enajenaciones» de los capítulos VI y VII de ingresos; la columna del capítulo VII (transferencias de capital de la Junta, "
             "300.000 € para Banca Pecho, concepto 750.80) se recoge como subvenciones. No hay remanente de tesorería afectado."))
save(f"A9 ANEXO DE INVERSIONES {YEAR}.xlsx", str(YEAR), rows)

# ---------------------------------------------------------------- A12 · subvenciones (p.123–128)
PART12 = re.compile(r"^(\d{4} \d{3}\.\d{2})\s+(" + IMP + r")\s+(.+?)\s*$")
progs12 = []
pr = None
bloque = "nominativas"
for p in range(123, 129):
    for line in PAGES[p - 1].splitlines():
        s = line.strip()
        if not s or s.startswith(("PARTIDA", "ENTIDAD", "En cumplimiento", "las subvenciones", "SUBVENCIONES NOMINATIVAS",
                                  "RELACIÓN DE ENTIDADES", "LA ALCALDESA", "Fdo.", "Presupuesto 2018")) or re.fullmatch(r"\d+", s):
            continue
        if s.startswith("APORTACIONES Y CUOTAS"):
            bloque, pr = "cuotas", None
            continue
        if m := PART12.match(s):
            pr = {"bloque": bloque, "partida": m.group(1), "credito": eur(m.group(2)), "programa": m.group(3), "items": [], "subtotal": None}
            progs12.append(pr)
            continue
        if m := re.fullmatch(r"(" + IMP + r")\s*€?", s):
            pr["subtotal"] = eur(m.group(1))
            continue
        partes = re.split(r"\s{2,}", s)
        assert len(partes) == 3 and re.fullmatch(IMP + r"\s*€?", partes[2]), (p, line)
        pr["items"].append({"entidad": partes[0], "objeto": partes[1], "importe": eur(partes[2].replace("€", "").strip())})
for pr in progs12:
    assert close(sum(i["importe"] for i in pr["items"]), pr["subtotal"]), pr["partida"]

rows = [(None,), (None, None, None, "SUBVENCIONES NOMINATIVAS"), (None,),
        (None, "PARTIDA", "CRÉDITO PARTIDA", "PROGRAMA", "OBJETO DEL CONVENIO", str(YEAR)),
        (None, None, None, "ENTIDAD BENEFICIARIA"), (None,)]
actual_bloque = "nominativas"
for pr in progs12:
    if pr["bloque"] != actual_bloque:
        rows += [(None,), (None, None, None, f"APORTACIONES Y CUOTAS {YEAR}"), (None,)]
        actual_bloque = pr["bloque"]
    rows.append((None, pr["partida"], pr["credito"], pr["programa"]))
    for it in pr["items"]:
        rows.append((None, None, None, it["entidad"], it["objeto"], it["importe"]))
    rows.append((None, None, None, None, pr["partida"].split()[0], pr["subtotal"]))
    rows.append((None,))
rows.append((None, f"Fuente: presupuesto municipal {YEAR} (PDF), p. 122-128. El anexo no trae el importe de {YEAR - 1}."))
save(f"A12 ANEXO SUBVENCIONES NOMINATIVAS {YEAR}.xlsx", str(YEAR), rows)

# ---------------------------------------------------------------- A13.1 / A13.2 · deuda (p.130–134)
# Transcrito a mano de p.130 (cuadro de 4 filas); cada cifra se comprueba con el texto y con los totales del cuadro.
p130 = PAGES[129]
prestamos = [
    # fecha, entidad, importe, primera, última, tipo, periodo, cuota trimestral, viva 31/12/2017, amortiz. 2018, viva 31/12/2018
    (datetime(2008, 10, 22), "CAJA MADRID", "1.161.000,00", datetime(2010, 12, 31), datetime(2020, 9, 30), "EURIBOR TRIM. +0,15%", "CTE. TRIM.", "20.621,66", "226.838,00", "82.486,64", "144.351,36"),
    (datetime(2009, 12, 1), "CAJA RURAL", "1.180.700,00", datetime(2011, 12, 31), datetime(2021, 9, 30), "EURIBOR SEM. + 0,95%", "CTE. TRIM.", "6.778,99", "101.684,95", "27.115,96", "74.568,99"),
    # Fila sin fecha ni entidad en el PDF: es el préstamo de 2017 (p.133). Fecha y entidad (BANKIA, 27/11/2017) del anexo de deuda de 2024.
    (datetime(2017, 11, 27), "BANKIA (3)", "362.528,65", datetime(2017, 12, 31), datetime(2027, 9, 30), "EURIBOR TRIM. +0,675%", "CTE. TRIM.", "9.063,22", "353.465,43", "36.252,87", "317.212,57"),
]
previsto = ("2018 (previsto)", "PREVISTO (2)", "2.491.062,38", None, None, "EURIBOR TRIM. +0,675%", "CTE. TRIM.", None, None, "0,00", "2.491.062,38")
for fila in prestamos + [previsto]:
    for v in fila:
        if isinstance(v, str) and re.fullmatch(IMP, v):
            assert v in p130, v
assert close(sum(eur(f[8]) for f in prestamos), eur("681.988,38"))
assert close(sum(eur(f[9]) for f in prestamos), eur("145.855,47")) and close(eur("145.855,47"), resumen["gastos"][9])
assert close(sum(eur(f[10]) for f in prestamos) + eur(previsto[10]), eur("3.027.195,30"))
for f in prestamos:
    assert abs(eur(f[8]) - eur(f[9]) - eur(f[10])) <= 0.011, f  # el PDF redondea 1 céntimo en el préstamo de 2017

def n(v):
    return eur(v) if isinstance(v, str) else v

rows = [(None,)] * 4 + [(None, None, None, None, None, None, "ANEXO DE DEUDA"), (None,),
        (None, None, None, None, None, None, None, f"             PRÉSTAMOS A LARGO PLAZO EN VIGOR A 31/12/{YEAR - 1}"), (None,),
        (None, None, "FECHA", "ENTIDAD", "IMPORTE", "PRIMERA AMORTIZ.", "ULTIMA AMORTIZ.", "TIPO DE INTERÉS", "AMORT.", "IMPORTE",
         f"DEUDA VIVA 01/01/{YEAR}", f"AMORTIZ. {YEAR}", f"DEUDA VIVA 31/12/{YEAR}"), (None,)]
for f in prestamos + [previsto]:
    rows.append((None, None, f[0], f[1], n(f[2]), f[3], f[4], f[5], f[6], n(f[7]), n(f[8]), n(f[9]), n(f[10])))
    rows.append((None,))
rows.append((None, None, None, None, None, None, None, None, None, eur("36.463,87"), eur("681.988,38"), eur("145.855,47"), eur("3.027.195,30")))
rows += [(None,),
         (None, None, f"No hay previsto solicitar operaciones de tesorería en {YEAR}"),
         (None, None, "Nota: la columna «DEUDA VIVA 01/01/2018» es la «DEUDA VIVA A 31/12/2017» del PDF (p. 130)."),
         (None, None, "(1) Caja Madrid: dispuesto 1.153.000,00 €. Caja Rural: dispuesto 927.427,52 € (amortización anticipada de 639.861,12 €)."),
         (None, None, "(2) Préstamo previsto en el presupuesto 2018 (capítulo IX de ingresos, 2.491.062,38 €) para pagar la sentencia PROINCOVE; el PDF no da fecha, entidad ni plazos."),
         (None, None, "(3) En el PDF esta fila no lleva fecha ni entidad; es el préstamo de 2017 (p. 133). Fecha y entidad tomadas del anexo de deuda de 2024.")]
save("A13.1 Estado de la deuda.xlsx", "AMORTIZACIONES", rows)

# Carga financiera: intereses de cada préstamo (p.131–134)
intereses = {"CAJA MADRID 2008": "957,24", "CAJA RURAL 2009": "1.182,83", "PRESTAMO 2017": "4.770,58", "PRESTAMO 2018 (PREVISTO)": "25.183,62"}
amortiz = {"CAJA MADRID 2008": "82.486,64", "CAJA RURAL 2009": "27.115,96", "PRESTAMO 2017": "36.252,87", "PRESTAMO 2018 (PREVISTO)": "0,00"}
texto_carga = "\n".join(PAGES[130:134])
for v in list(intereses.values()) + [a for a in amortiz.values() if a != "0,00"] + ["32.094,27", "145.855,47"]:
    assert v in texto_carga, v
en_vigor = round(sum(eur(v) for k, v in intereses.items() if "PREVISTO" not in k), 2)
con_previsto = round(sum(eur(v) for v in intereses.values()), 2)
assert close(con_previsto, eur("32.094,27"))
rows = [(None, None, f"PREVISIÓN CARGA FINANCIERA {YEAR}"), (None,)]
for k in intereses:
    rows.append((None, k, None, None, None, f"INTERESES {k}", eur(intereses[k])))
    rows.append((None, None, None, None, None, f"AMORTIZ. {k}", eur(amortiz[k])))
    rows.append((None,))
rows += [(None, None, None, None, None, f"TOTAL INTERESES {YEAR}", en_vigor),
         (None, None, None, None, None, f"TOTAL  AMORTIZACIÓN {YEAR}", eur("145.855,47")),
         (None,),
         (None, None, None, None, None, f"TOTAL INTERESES {YEAR} CON EL PRÉSTAMO PREVISTO", con_previsto),
         (None,),
         (None, f"Fuente: presupuesto municipal {YEAR} (PDF), p. 131-134. El PDF da un único total de intereses (32.094,27 €) que incluye "
                f"el préstamo previsto de 2018; el total sin él ({en_vigor:.2f} €) es la suma de los intereses de los otros tres préstamos.")]
save("A13.2 Carga Financiera.xlsx", "Hoja1", rows)

# ---------------------------------------------------------------- informe
print("Gastos: partidas", len(gastos), "| sin importe (no se pasan):", [(g["pagina"], g["codigo"], g["nombre"]) for g in sin_importe])
print("Líneas de detalle ignoradas (sin código, tras una partida con importe):")
for d in detalles:
    print("  p.%d  %s" % d)
print("Totales de programa con otro código en el rótulo:", rotulos_raros)
print("Ingresos: conceptos", sum(len(a["conceptos"]) for c in ingresos.values() for a in c))
print("Artículos con rótulo de total distinto del código:", [x for x in art_total_pdf if x[1] != x[2]])
print("Inversiones: proyectos", sum(len(p["proyectos"]) for p in programas9), "total", total9)
print("Subvenciones:", {b: round(sum(i["importe"] for p in progs12 if p["bloque"] == b for i in p["items"]), 2) for b in ("nominativas", "cuotas")},
      "entidades", sum(len(p["items"]) for p in progs12))
print("Deuda viva 31/12/2018 (sin previsto):", round(sum(eur(f[10]) for f in prestamos), 2), "intereses", en_vigor, con_previsto)
print("Gastos", sum(resumen["gastos"].values()), "Ingresos", sum(resumen["ingresos"].values()))
