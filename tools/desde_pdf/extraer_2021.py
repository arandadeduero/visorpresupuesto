"""Extrae los anexos del presupuesto 2021 (PDF → texto con pdftotext -layout) a los xlsx que leen tools/budget."""
import re
import sys
from pathlib import Path
import openpyxl

# Uso: python -I extraer_2021.py <2021.txt> <carpeta_salida>
PAGES = Path(sys.argv[1]).read_text().split("\f")
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
YEAR = 2021
AMT = r"(-?[\d.]+,\d{2}) ?€"
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]


def eur(s):
    return round(float(s.replace(".", "").replace(",", ".")), 2)


def lines(p1, p2):
    for p in range(p1, p2 + 1):
        for l in PAGES[p - 1].splitlines():
            if l.strip():
                yield p, l


def save(rows, name, sheet=str(YEAR)):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    for r in rows:
        ws.append(list(r))
    wb.save(OUT / name)


# ---------- Resumen (p.4) ----------
def resumen():
    txt = PAGES[3]
    g, i = txt.split("INGRESOS\n", 1)

    def caps(t):
        out = {}
        for m in re.finditer(r"CAP[IÍ]TULO ([IVX]+):\s+(.+?)(?:\s{2,}" + AMT + r")?$", t, re.M):
            out[ROMAN.index(m.group(1))] = (m.group(2).strip(), eur(m.group(3)) if m.group(3) else 0.0)
        return out

    tg = eur(re.search(r"TOTAL ESTADO DE GASTOS\s+" + AMT, txt).group(1))
    ti = eur(re.search(r"TOTAL ESTADO DE INGRESOS\s+" + AMT, txt).group(1))
    return caps(g), caps(i), tg, ti


def write_a1(gc, ic, tg, ti):
    assert set(gc) == set(range(1, 10)) and set(ic) == set(range(1, 10)), (gc, ic)
    assert abs(sum(v for _, v in gc.values()) - tg) < 0.01 and abs(sum(v for _, v in ic.values()) - ti) < 0.01
    rows = [(), (None, f"PRESUPUESTO GENERAL AYUNTAMIENTO {YEAR}"), (None, "ESTADO DE GASTOS"),
            (None, "CAP. ", "DESCRIPCIÓN", f"PREVISIONES {YEAR}", f"CRÉDITOS {YEAR - 1}")]
    rows += [(None, n, gc[n][0], gc[n][1], None) for n in range(1, 10)]
    rows += [(None, "TOTAL GASTOS", None, tg, None), (), (None, "ESTADO DE INGRESOS"),
             (None, "CAP. ", "DESCRIPCIÓN", f"PREVISIONES {YEAR}", f"CRÉDITOS {YEAR - 1}")]
    rows += [(None, n, ic[n][0], ic[n][1], None) for n in range(1, 10)]
    rows += [(None, "TOTAL INGRESOS", None, ti, None)]
    save(rows, f"A1 RESUMEN POR CAPITULOS {YEAR}.xlsx")


# ---------- Gastos (p.5-64) ----------
SKIP = re.compile(r"^(Clasificaci|PRESUPUESTO|Presupuesto \d{4}|\d{4}$|CAP[IÍ]TULO [IVX]+\s*$|PERSONAL |CARGOS ELECTOS|PRESTACIONES SOCIALES$|GASTOS DE PERSONAL$)")
CODE = re.compile(r"(\d{2,3}(?:\.\d{2})?)\s+(\D.*?)(?:\s+" + AMT + ")?$")


def gastos(caps_ref):
    """{cap: [(programa, nombre_programa, codigo, nombre, importe)]}; comprueba cada TOTAL del PDF."""
    out, cap, prog = {}, None, None
    state = "idle"  # idle | progname | articulo | partida
    cur = None
    bloque, problemas, names, parts = [], [], {}, []

    def cierra():
        nonlocal cur
        if cur:
            if cur[2] is None:
                problemas.append(f"partida sin importe {cur}")
            out[cap].append((prog, names[prog], cur[0], " ".join(cur[1].split()), cur[2] or 0.0))
            bloque.append(cur[2] or 0.0)
            cur = None

    for p, raw in lines(5, 64):
        l = raw.strip()
        if m := re.match(r"CAP[IÍ]TULO ([IVX]+)\s*:", l):
            if not l.startswith("CAPÍTULO I:    "):  # p.6: «CAPÍTULO I:  12.287.605,91 €» es portada
                cap = ROMAN.index(m.group(1)); out.setdefault(cap, []); state = "idle"
            continue
        if m := re.match(r"TOTAL CAP[IÍ]TULO ([IVX]+):?\s+" + AMT + "$", l):
            cierra(); n = ROMAN.index(m.group(1))
            s = round(sum(x[4] for x in out[n]), 2)
            if abs(s - eur(m.group(2))) > 0.005 or abs(s - caps_ref[n]) > 0.005:
                problemas.append(f"cap {n}: partidas {s} vs PDF {m.group(2)} vs resumen {caps_ref[n]}")
            state = "idle"; continue
        if m := re.match(r"TOTAL ?(\d{4})\s+" + AMT + "$", l):
            cierra()
            if abs(sum(bloque) - eur(m.group(2))) > 0.005:
                problemas.append(f"p.{p} programa {prog} (rótulo TOTAL {m.group(1)}): {round(sum(bloque), 2)} vs {m.group(2)}")
            if m.group(1) != prog:
                print(f"  nota p.{p}: rótulo «TOTAL {m.group(1)}» bajo el programa {prog}")
            bloque.clear(); state = "idle"; continue
        if l.startswith("TOTAL "):
            cierra(); state = "idle"; continue
        if re.fullmatch(r"\d{4}", l) and cap is not None:
            cierra(); prog = l; state = "progname"; names.setdefault(prog, ""); parts = []; continue
        if l.startswith("Clasificaci") or re.match(r"Presupuesto \d{4}", l):
            continue
        if state != "progname" and SKIP.match(l):
            continue
        m = CODE.match(l)
        if m and prog and cap:
            cierra()
            if state == "progname":
                names[prog] = names[prog] or " ".join(parts)
            if len(m.group(1)) == 2:
                state = "articulo"; continue
            cur = [m.group(1), m.group(2), eur(m.group(3)) if m.group(3) else None]
            state = "partida"; continue
        if state == "progname":
            parts.append(l); continue
        if state == "partida" and cur:
            if mm := re.match(r"(.*?)\s*" + AMT + "$", l):
                if cur[2] is not None:
                    problemas.append(f"p.{p} importe de más: {l!r}")
                cur[1] += " " + mm.group(1); cur[2] = eur(mm.group(2))
            else:
                cur[1] += " " + l
            continue
        if state == "articulo" and not re.search(AMT + "$", l):
            continue
        if re.search(AMT + "$", l):
            problemas.append(f"p.{p} línea con importe ignorada: {l!r}")
    return out, problemas


def write_a3(g):
    rows = []
    for cap in range(1, 10):
        rows += [(), (None, "CLASIFICACIÓN", None, f"CAPITULO {ROMAN[cap]}"), (None, "PROGRAMA", "ECONÓMICA", None, None, YEAR - 1, YEAR)]
        prev = None
        for prog, pname, cod, nombre, imp in g.get(cap, []):
            if prog != prev:
                rows.append((None, prog, None, pname, None, YEAR - 1, YEAR))
                prev = prog
            rows.append((None, None, cod, nombre, None, None, imp))
        rows.append((None, None, None, f"TOTAL CAPÍTULO {ROMAN[cap]}", None, None, round(sum(x[4] for x in g.get(cap, [])), 2)))
    save(rows, f"A3 ESTADO DE GASTOS {YEAR}.xlsx")


# ---------- Ingresos (p.66-83) ----------
def ingresos(caps_ref):
    """{cap: (titulo, [(codigo, nombre, importe)])}; comprueba TOTAL ARTÍCULO y TOTAL CAPÍTULO."""
    out, cap, cur, art, problemas = {}, None, None, [], []

    def cierra():
        nonlocal cur
        if cur:
            if cur[2] is None:
                problemas.append(f"concepto sin importe {cur}")
            out[cap][1].append((cur[0], " ".join(cur[1].split()), cur[2] or 0.0))
            art.append(cur[2] or 0.0)
            cur = None

    for p, raw in lines(66, 83):
        l = raw.strip()
        if m := re.match(r"CAP[IÍ]TULO ([IVX]+):\s+(.+)$", l):
            cap = ROMAN.index(m.group(1)); out[cap] = (m.group(2).strip(), []); continue
        if m := re.match(r"TOTAL ART[IÍ]CULO (\d\d)\s+" + AMT + "$", l):
            cierra()
            if abs(sum(art) - eur(m.group(2))) > 0.005:
                problemas.append(f"p.{p} artículo {m.group(1)}: {sum(art)} vs {m.group(2)}")
            art.clear(); continue
        if m := re.match(r"TOTAL CAP[IÍ]TULO ([IVX]+):?\s+" + AMT + "$", l):
            cierra(); n = ROMAN.index(m.group(1)); s = round(sum(x[2] for x in out[n][1]), 2)
            if abs(s - eur(m.group(2))) > 0.005 or abs(s - caps_ref[n]) > 0.005:
                problemas.append(f"cap {n}: {s} vs {m.group(2)} vs resumen {caps_ref[n]}")
            cap = None; continue
        if cap is None or l.startswith("Clasificaci") or re.match(r"Presupuesto \d{4}", l):
            continue
        if m := re.match(r"(\d{3}(?:[.,]\d{2})?)\s+(\D.*?)(?:\s+" + AMT + ")?$", l):
            cierra(); cur = [m.group(1).replace(",", "."), m.group(2), eur(m.group(3)) if m.group(3) else None]; continue
        if re.fullmatch(r"\d\d", l):
            cierra(); continue
        if cur:
            if mm := re.match(r"(.*?)\s*" + AMT + "$", l):
                if cur[2] is not None:
                    problemas.append(f"p.{p} importe de más {l!r}")
                cur[1] += " " + mm.group(1); cur[2] = eur(mm.group(2))
            elif re.match(r"[a-z(]", l):  # continuación del nombre del concepto (minúscula o paréntesis)
                cur[1] += " " + l
            else:  # rótulo de artículo en mayúsculas («TRANSFERENCIAS CORRIENTES…»)
                cierra()
        elif re.search(AMT + "$", l):
            problemas.append(f"p.{p} línea con importe ignorada {l!r}")
    return out, problemas


def write_a2(ing):
    rows = []
    for cap, (titulo, conceptos) in sorted(ing.items()):
        rows += [(None, "CLASIFIC. ECONÓMICA", f"CAPÍTULO {ROMAN[cap]}: {titulo}", f"AÑO {YEAR}")]
        rows += [(None, c, n, v) for c, n, v in conceptos]
        rows += [(None, None, f"TOTAL CAPÍTULO {ROMAN[cap]}", round(sum(v for *_, v in conceptos), 2)), ()]
    save(rows, f"A2 ESTADO DE INGRESOS {YEAR}.xlsx")


# ---------- Subvenciones nominativas y cuotas (p.111-116) ----------
def subvenciones():
    rows = [(None, "SUBVENCIONES NOMINATIVAS"), (), (None, "PARTIDA", "CRÉDITO PARTIDA", "PROGRAMA", "OBJETO DEL CONVENIO", str(YEAR)),
            (None, None, None, "ENTIDAD BENEFICIARIA")]
    problemas, bloque, totales, n_items = [], [], {"nominativas": 0.0, "cuotas": 0.0}, 0
    tipo = "nominativas"
    for p, raw in lines(111, 116):
        l = raw.strip()
        if l.startswith(("En cumplimiento", "las subvenciones", "SUBVENCIONES NOMINATIVAS", "PARTIDA", "ENTIDAD", "RELACIÓN DE ENTIDADES")) or re.match(r"Presupuesto \d{4}", l):
            continue
        if l.startswith("APORTACIONES Y CUOTAS"):
            tipo = "cuotas"
            rows += [(), (None, None, None, "APORTACIONES Y CUOTAS ASOCIACIONES"), (),
                     (None, "PARTIDA", "CRÉDITO PARTIDA", "PROGRAMA", "CONCEPTO", str(YEAR))]
            continue
        if m := re.fullmatch(AMT, l):  # subtotal del programa
            if abs(sum(bloque) - eur(m.group(1))) > 0.005:
                problemas.append(f"p.{p} subtotal {m.group(1)} vs {sum(bloque)}")
            bloque.clear(); continue
        if m := re.match(r"(\d{4} \d{3}\.\d{2})\s+([\d.]+,\d{2})\s+(.*)$", l):
            partes = re.split(r"\s{2,}", m.group(3))
            if len(partes) == 1:  # programa
                rows.append((None, m.group(1), eur(m.group(2)), partes[0]))
            else:  # la fila de la partida es también la entidad (TURISMO)
                ent, obj, imp = partes
                rows.append((None, m.group(1), eur(m.group(2)), ent, obj, eur(re.fullmatch(AMT, imp).group(1))))
                bloque.append(rows[-1][5]); totales[tipo] += rows[-1][5]; n_items += 1
            continue
        partes = re.split(r"\s{2,}", l)
        if len(partes) == 3 and re.fullmatch(AMT, partes[2]):
            ent, obj, imp = partes
            rows.append((None, None, None, ent, obj, eur(re.fullmatch(AMT, imp).group(1))))
            bloque.append(rows[-1][5]); totales[tipo] += rows[-1][5]; n_items += 1
        elif len(partes) == 1 and not re.search(r"\d", l):
            rows.append((None, None, None, l))  # título («TURISMO»)
        else:
            problemas.append(f"p.{p} línea no reconocida {l!r}")
    save(rows, f"A12 ANEXO SUBVENCIONES NOMINATIVAS {YEAR}.xlsx")
    return totales, n_items, problemas


# ---------- Inversiones (p.118-119) ----------
INV_COLS = ["importe", "prestamo", "ingresosCorrientes", "enajenacion", "subvenciones", "total"]


def _importes(l):
    return [(m.end(), eur(m.group(1))) for m in re.finditer(AMT, l)]


def inversiones(cap6):
    progs, prog, partida, pend, problemas, total = [], None, None, [], [], None
    state = None
    for p, raw in lines(118, 119):
        l = raw.strip()
        if l.startswith("PROYECTOS PLURIANUALES"):
            break
        if l.startswith(("PARTIDA/C", "PROYECTO", "ÓDIGO")) or re.match(r"Presupuesto \d{4}", l):
            continue
        if l.startswith("TOTAL CAPITULO VI"):
            total = [v for _, v in _importes(raw)]; continue
        if re.fullmatch(r"\d{4}", l):
            prog = {"codigo": l, "nombre": [], "partidas": []}; progs.append(prog); state = "nombre"; continue
        if m := re.match(r"(\d{3})\s+(\D.*)$", l):
            partida = (m.group(1), m.group(2).strip(), []); prog["partidas"].append(partida); state = None; continue
        if m := re.match(r"(\d{3}/\d{4})\s+(.*?)\s{2,}" + AMT, l):
            partida[2].append((m.group(1), m.group(2), raw)); continue
        if re.fullmatch(r"(" + AMT + r"\s*)+", l):  # subtotal del programa: fija la posición de las columnas
            ends = _importes(raw)
            if len(ends) != 6:
                problemas.append(f"p.{p} subtotal con {len(ends)} columnas"); continue
            prog["subtotal"] = [v for _, v in ends]
            for _, _, proys in prog["partidas"]:
                for i, (cod, nom, r) in enumerate(proys):
                    vals = dict.fromkeys(INV_COLS, 0.0)
                    for end, v in _importes(r):
                        col = min(range(6), key=lambda k: abs(ends[k][0] - end))
                        vals[INV_COLS[col]] += v
                    proys[i] = (cod, nom, vals)
            continue
        if state == "nombre":
            prog["nombre"].append(l); continue
        problemas.append(f"p.{p} línea no reconocida {l!r}")
    # comprobaciones
    for pr in progs:
        proys = [v for *_, ps in pr["partidas"] for (_, _, v) in ps]
        for k, c in enumerate(INV_COLS):
            s = round(sum(v[c] for v in proys), 2)
            if abs(s - pr["subtotal"][k]) > 0.005:
                problemas.append(f"programa {pr['codigo']} columna {c}: {s} vs {pr['subtotal'][k]}")
        for v in proys:
            if abs(v["importe"] - v["total"]) > 0.005 or abs(sum(v[c] for c in INV_COLS[1:5]) - v["importe"]) > 0.005:
                problemas.append(f"proyecto con fuentes que no suman: {v}")
    for k, c in enumerate(INV_COLS):
        s = round(sum(pr["subtotal"][k] for pr in progs), 2)
        if abs(s - total[k]) > 0.005:
            problemas.append(f"TOTAL CAPITULO VI columna {c}: {s} vs {total[k]}")
    if abs(total[0] - cap6) > 0.005:
        problemas.append(f"inversiones {total[0]} vs capítulo 6 {cap6}")
    # A9: la enajenación de inversiones (0 € en 2021) va en «OTROS»; no hay remanente afectado (RTA) en 2021
    rows = [(f"ANEXO INVERSIONES REALES {YEAR}",), (),
            ("PARTIDA/CÓDIGO", "PROYECTO", "IMPORTE", "PRÉSTAMO", "INGRESOS CORRIENTES", "OTROS", "REMANENTE DE TESORERÍA AFECTADO (CAP 8)", "SUBVENCIONES", "TOTAL"), ()]
    n = 0
    for pr in progs:
        rows.append((pr["codigo"], " ".join(pr["nombre"])))
        for cod, nom, proys in pr["partidas"]:
            rows.append((cod, nom))
            for pc, pn, v in proys:
                rows.append((pc, pn, v["importe"], v["prestamo"], v["ingresosCorrientes"], v["enajenacion"], 0, v["subvenciones"], v["total"]))
                n += 1
        st = pr["subtotal"]
        rows += [(None, pr["codigo"], st[0], st[1], st[2], st[3], 0, st[4], st[5]), ()]
    rows.append((None, "TOTAL CAPITULO VI", total[0], total[1], total[2], total[3], 0, total[4], total[5]))
    save(rows, f"A9 ANEXO DE INVERSIONES {YEAR}.xlsx")
    return total, n, problemas


# ---------- Deuda (p.120-122) ----------
def deuda():
    from datetime import datetime as dt
    d = lambda s: dt.strptime(s, "%d/%m/%Y")
    hdr = (None, None, "FECHA", "ENTIDAD", "IMPORTE", "PRIMERA AMORTIZ.", "ULTIMA AMORTIZ.", "TIPO DE INTERÉS", "AMORT.", "IMPORTE",
           f"DEUDA VIVA 01/01/{YEAR}", f"AMORTIZ. {YEAR}", f"DEUDA VIVA 31/12/{YEAR}")
    rows = [(None, None, None, None, None, None, "ANEXO DE DEUDA"), (),
            (None, None, None, None, None, None, None, f"PRÉSTAMOS A LARGO PLAZO EN VIGOR A 31/12/{YEAR - 1} Y PRÉSTAMO PREVISTO EN {YEAR}"), (), hdr, ()]
    pat = re.compile(r"(\S+)\s+(.+?)\s+([\d.]+,\d{2})\s+(\d\d/\d\d/\d{4})\s+(\d\d/\d\d/\d{4})\s+(EURIBOR.+?)\s+(CTE\. (?:TRIM|ANUAL)\.?)\s+([\d.]+,\d{2})\s+([\d.]+,\d{2})\s+([\d.]+,\d{2})\s+([\d.]+,\d{2})$")
    problemas, suma = [], [0.0, 0.0, 0.0]
    for l in PAGES[119].splitlines():
        m = pat.match(l.strip())
        if not m:
            continue
        f, ent, imp, pri, ult, tipo, per, cuota, v0, am, v1 = m.groups()
        if ent.strip() == "---":
            fecha, ent = f"{f} (previsto)", "PREVISTO"
            tipo = "EURIBOR TRIM. +0,675%"  # la tabla de p.120 deja el diferencial en blanco («+ _____»); el cálculo de p.122 usa +0,675%
        else:
            fecha = d(f)
            suma = [suma[0] + eur(v0), suma[1] + eur(am), suma[2] + eur(v1)]
        rows += [(None, None, fecha, ent.strip(), eur(imp), d(pri), d(ult), " ".join(tipo.split()), per, eur(cuota), eur(v0), eur(am), eur(v1)), ()]
    tot = re.search(r"^\s+([\d.]+,\d{2})\s+([\d.]+,\d{2})\s+([\d.]+,\d{2})\s*$", PAGES[119], re.M).groups()
    if any(abs(a - eur(b)) > 0.005 for a, b in zip(suma, tot)):
        problemas.append(f"deuda: suma {suma} vs total {tot}")
    rows += [(None, None, None, None, None, None, None, None, None, None, *[round(x, 2) for x in suma])]
    rows += [(), (None, None, f"No hay operaciones de tesorería pendientes, ni está previsto solicitarlas en {YEAR}")]
    save(rows, "A13.1 Estado de la deuda.xlsx", "AMORTIZACIONES")
    txt = PAGES[121]
    ti = eur(re.search(r"TOTAL INTERESES\s+([\d.]+,\d{2})", txt).group(1))
    ta = eur(re.search(r"TOTAL AMORTIZACIÓN\s+([\d.]+,\d{2})", txt).group(1))
    if abs(ta - suma[1]) > 0.005:
        problemas.append(f"carga: amortización {ta} vs anexo de deuda {suma[1]}")
    save([(None, None, f"PREVISIÓN CARGA FINANCIERA {YEAR}"), (),
          (None, None, None, None, None, f"TOTAL INTERESES {YEAR}", ti),
          (None, None, None, None, None, f"TOTAL  AMORTIZACIÓN {YEAR}", ta)], "A13.2 Carga Financiera.xlsx", "Hoja1")
    return suma, ti, ta, len(rows), problemas


if __name__ == "__main__":
    gc, ic, tg, ti = resumen()
    print("resumen gastos", gc, tg)
    print("resumen ingresos", ic, ti)
    write_a1(gc, ic, tg, ti)
    g, prob = gastos({n: v for n, (_, v) in gc.items()})
    for x in prob:
        print("PROBLEMA gastos:", x)
    print("partidas gastos:", {c: len(v) for c, v in g.items()}, sum(len(v) for v in g.values()))
    write_a3(g)
    ing, prob = ingresos({n: v for n, (_, v) in ic.items()})
    for x in prob:
        print("PROBLEMA ingresos:", x)
    print("conceptos ingresos:", {c: len(v[1]) for c, v in ing.items()}, sum(len(v[1]) for v in ing.values()))
    write_a2(ing)
    tot, n, prob = subvenciones()
    for x in prob:
        print("PROBLEMA subvenciones:", x)
    print("subvenciones:", tot, "entidades:", n)
    tot, n, prob = inversiones(gc[6][1])
    for x in prob:
        print("PROBLEMA inversiones:", x)
    print("inversiones:", dict(zip(INV_COLS, tot)), "proyectos:", n)
    suma, ti_, ta, _, prob = deuda()
    for x in prob:
        print("PROBLEMA deuda:", x)
    print("deuda (01/01, amort, 31/12):", suma, "intereses", ti_, "amortización", ta)
