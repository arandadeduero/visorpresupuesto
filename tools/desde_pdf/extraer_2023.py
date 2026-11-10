"""Extrae los anexos del presupuesto 2023 (PDF ya pasado a texto con `pdftotext -layout`) a los Excel que leen
los parsers de tools/budget. Uso: python extraer_2023.py <2023.txt> <carpeta_salida>

Cada bloque comprueba sus subtotales contra los que trae el propio PDF (assert)."""
import re
import sys
from datetime import datetime
from pathlib import Path

import openpyxl

TXT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
PAG = TXT.read_text().split("\f")
AMT = r"-?\d{1,3}(?:\.\d{3})*,\d\d"
YEAR = 2023


def pag(n):
    return PAG[n - 1].splitlines()


def eur(s):
    return round(float(s.replace("€", "").strip().replace(".", "").replace(",", ".")), 2)


def guarda(nombre, hoja, filas):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = hoja
    for f in filas:
        ws.append(list(f))
    wb.save(OUT / nombre)


def cerca(a, b):
    return abs(a - b) < 0.015


# ---------------------------------------------------------------- A1 (p. 2)
def a1():
    filas = [(None, f"PRESUPUESTO GENERAL AYUNTAMIENTO {YEAR}")]
    tot = {}
    for l in pag(2):
        s = l.strip()
        if s.startswith("ESTADO DE"):
            filas.append((None, s))
        elif s.startswith("CAP."):
            filas.append((None, "CAP. ", "DESCRIPCIÓN", f"PREVISIONES {YEAR}", f"CRÉDITOS {YEAR - 1}"))
        elif m := re.match(rf"^(\d)\s+(.+?)\s+({AMT}) €\s+({AMT}) €$", s):
            filas.append((None, float(m[1]), m[2].strip(), eur(m[3]), eur(m[4])))
        elif m := re.match(rf"^(TOTAL [A-Z. ]+?)\s+({AMT}) €\s+({AMT}) €$", s):
            etiqueta = m[1].strip()
            col = 1 if etiqueta in ("TOTAL GASTOS", "TOTAL INGRESOS") else 2
            fila = [None] * 5
            fila[col], fila[3], fila[4] = etiqueta, eur(m[2]), eur(m[3])
            filas.append(tuple(fila))
            tot.setdefault(etiqueta, []).append(eur(m[2]))
    caps = [f for f in filas if isinstance(f[1], float)]
    assert len(caps) == 18, len(caps)
    g, i = caps[:9], caps[9:]
    assert cerca(sum(f[3] for f in g), tot["TOTAL GASTOS"][0]) and cerca(sum(f[3] for f in i), tot["TOTAL INGRESOS"][0])
    assert cerca(sum(f[4] for f in g), 36358359.00)
    guarda(f"A1 RESUMEN POR CAPITULOS {YEAR}.xlsx", str(YEAR), filas)
    return {int(f[1]): f[3] for f in g}, {int(f[1]): f[3] for f in i}


# ---------------------------------------------------------------- A2 (p. 3-4)
def a2(ref):
    filas, conceptos, totales = [], {}, {}
    cap = None
    for n in (3, 4):
        for l in pag(n):
            s = l.strip()
            if m := re.match(r"^(CAP[IÍ]TULO ([IVX]+):.*?)\s+PREVISIONES$", s):
                cap = m[2]
                filas.append((None, "CLASIFIC. ECONÓMICA", m[1], f"AÑO {YEAR}"))
            elif m := re.match(rf"^(\d{{3}}(?:\.\d\d)?)\s+(.+?)\s+({AMT}) €$", s):
                filas.append((None, m[1], m[2], eur(m[3])))
                conceptos.setdefault(cap, []).append(eur(m[3]))
            elif m := re.match(rf"^(ART[IÍ]CULO \d\d)\s+({AMT}) €$", s):
                filas.append((None, None, m[1], eur(m[2])))
            elif m := re.match(rf"^(TOTAL CAP[IÍ]TULO ([IVX]+))\s+({AMT}) €$", s):
                filas.append((None, None, m[1], eur(m[3])))
                totales[m[2]] = eur(m[3])
            elif "PREVISIONES TOTALES" in s:
                filas.append((None, None, "PREVISIONES TOTALES ESTADO DE INGRESOS", eur(re.search(AMT, s)[0])))
    rom = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9}
    for c, v in totales.items():
        assert cerca(sum(conceptos[c]), v), (c, sum(conceptos[c]), v)
        assert cerca(v, ref[rom[c]]), c
    print("A2 conceptos:", sum(len(v) for v in conceptos.values()))
    guarda(f"A2 ESTADO DE INGRESOS {YEAR}.xlsx", str(YEAR), filas)


# ---------------------------------------------------------------- A3 (p. 5-27)
def a3(ref):
    filas = [(None, "CLASIFICACIÓN", None, None), (None, "PROGRAMA", "ECONÓMICA")]
    cap = prog = None
    suma_prog = {}
    por_cap, totales = {}, {}
    avisos = []
    n_partidas = 0
    for n in range(5, 28):
        for l in pag(n):
            s = l.strip()
            if m := re.match(r"^CAPITULO ([IVX]+)$", s):
                cap = m[1]
                filas.append((None, "CLASIFICACIÓN", None, f"CAPITULO {cap}"))
            elif m := re.match(r"^(\d{4})\s+(.+?)\s+2023$", s):
                prog = m[1]
                filas.append((None, prog, None, m[2], None, YEAR - 1, YEAR))
                suma_prog.setdefault((cap, prog), 0.0)
            elif m := re.match(rf"^(\d{{3}}(?:\.\d\d)?)\s+(.+?)\s+({AMT}) €$", s):
                v = eur(m[3])
                filas.append((None, None, m[1], m[2], None, None, v))
                suma_prog[(cap, prog)] += v
                por_cap[cap] = por_cap.get(cap, 0.0) + v
                n_partidas += 1
            elif m := re.match(rf"^(?:(\d{{4}})\s+)?({AMT}) €$", s):  # subtotal de programa (en el cap. VI sin código)
                v = eur(m[2])
                if m[1] and m[1] != prog:
                    avisos.append(f"A3 cap. {cap}: el subtotal lleva el código {m[1]} pero el programa es {prog}")
                filas.append((None, m[1] or prog, None, None, None, None, v))
                if not cerca(suma_prog[(cap, prog)], v):
                    # programa partido entre páginas con cabecera repetida: se sigue sumando sobre el mismo
                    raise AssertionError(f"Subtotal {cap} {prog}: {suma_prog[(cap, prog)]} != {v}")
                suma_prog[(cap, prog)] = 0.0
            elif m := re.match(rf"^(TOTAL CAPÍTULO ([IVX]+))\s+({AMT}) €$", s):
                totales[m[2]] = eur(m[3])
                filas.append((None, None, None, m[1], None, None, eur(m[3])))
    rom = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9}
    for c, v in totales.items():
        if c == "I":  # descuadre del propio PDF: las partidas (y los subtotales de programa) suman 82.600 € menos
            assert cerca(v - por_cap[c], 82600), (c, por_cap[c], v)
            avisos.append(f"A3 cap. I: partidas {por_cap[c]:.2f} y TOTAL CAPÍTULO I {v:.2f} (diferencia {v - por_cap[c]:.2f})")
        else:
            assert cerca(por_cap[c], v), (c, por_cap[c], v)
        assert cerca(v, ref[rom[c]]), c
    assert len(totales) == 9
    print("A3 partidas:", n_partidas, *avisos, sep="\n  ")
    guarda(f"A3 ESTADO DE GASTOS {YEAR}.xlsx", str(YEAR), filas)


# ---------------------------------------------------------------- A9 (p. 107-109)
def a9(ref6):
    cab = ["PARTIDA/CÓDIGO", "PROYECTO", "IMPORTE", "PRÉSTAMO", "INGRESOS CORRIENTES", "OTROS (ENAJEN. INVERSIONES)",
           "RTA (CAP 8)", "SUBVENC.", "TOTAL"]
    cols_pdf = [2, 3, 4, 5, 7, 8]  # importe, préstamo, ing. corrientes, enajenación, subvenciones, total (el PDF no trae RTA)
    filas = [(f"ANEXO INVERSIONES REALES {YEAR}",), tuple(cab)]
    acum = [0.0] * 9
    total = [0.0] * 9
    n_proy = 0
    for n in (107, 108, 109):
        lineas = pag(n)
        # posiciones (fin de cada importe) de las 6 columnas, tomadas de una fila de subtotal de la página
        ref_pos = None
        for l in lineas:
            ms = list(re.finditer(rf"{AMT} ?€", l))
            if len(ms) == 6:
                ref_pos = [x.end() for x in ms]
                break
        for l in lineas:
            s = l.strip()
            ms = list(re.finditer(rf"({AMT}) ?€", l))
            if m := re.match(r"^(\d{4}) ([A-ZÁÉÍÓÚÑ].+)$", s):
                filas.append((m[1], m[2]))
            elif m := re.match(r"^(\d{3}) (\S.+)$", s):
                filas.append((m[1], m[2]))
            elif m := re.match(r"^(\S+/\d{4})\s+(.+?)\s{2,}" + AMT, s):
                fila = [None] * 9
                fila[0], fila[1] = m[1], m[2].strip()
                fila[2], fila[8] = eur(ms[0][1]), eur(ms[-1][1])
                for x in ms[1:-1]:
                    k = min(range(1, 5), key=lambda i: abs(ref_pos[i] - x.end()))
                    assert fila[cols_pdf[k]] is None, l
                    fila[cols_pdf[k]] = eur(x[1])
                assert cerca(fila[2], fila[8]) and cerca(sum(fila[c] or 0 for c in (3, 4, 5, 7)), fila[2]), l
                filas.append(tuple(fila))
                for c in range(2, 9):
                    acum[c] += fila[c] or 0
                n_proy += 1
            elif len(ms) == 6:
                vals = [eur(x[1]) for x in ms]
                fila = [None] * 9
                for c, v in zip(cols_pdf, vals):
                    fila[c] = v
                fila[6] = 0
                es_total = s.startswith("TOTAL CAPITULO VI")
                for c, v in zip(cols_pdf, vals):
                    got = total[c] if es_total else acum[c]
                    assert cerca(got, v), (s, c, got, v)
                if es_total:
                    fila[1] = "TOTAL CAPITULO VI"
                    filas.append(tuple(fila))
                    assert cerca(vals[0], ref6)
                    print("A9 proyectos:", n_proy, "total", vals)
                    guarda(f"A9 ANEXO DE INVERSIONES {YEAR}.xlsx", str(YEAR), filas)
                    return
                fila[1] = s.split()[0]  # «1320»: subtotal del programa
                filas.append(tuple(fila))
                total = [a + b for a, b in zip(total, acum)]
                acum = [0.0] * 9
    raise AssertionError("A9 sin total")


# ---------------------------------------------------------------- A12 (p. 115-119)
def a12():
    filas = [(None, None, None, "SUBVENCIONES NOMINATIVAS"),
             (None, "PARTIDA", "CRÉDITO PARTIDA", "PROGRAMA", "OBJETO DEL CONVENIO", str(YEAR)),
             (None, None, None, "ENTIDAD BENEFICIARIA")]
    suma = 0.0
    bloque_sum = {}
    bloque = "nominativas"
    prog_actual = None
    n_ent = 0
    for n in range(115, 120):
        for l in pag(n):
            s = l.strip()
            if not s or "Presupuesto Ayuntamiento" in s or s.startswith(("CRÉDITO", "PARTIDA", "SUBVENCIONES NOMINATIVAS")):
                continue
            if s.startswith("APORTACIONES Y CUOTAS"):
                bloque = "cuotas"
                filas += [(None, None, None, "APORTACIONES Y CUOTAS ASOCIACIONES"),
                          (None, "PARTIDA", "CRÉDITO PARTIDA", "PROGRAMA", "CONCEPTO", str(YEAR)),
                          (None, None, None, "ENTIDAD BENEFICIARIA")]
                continue
            if m := re.match(rf"^TOTAL SUBVENCIONES NOMINATIVAS\s+({AMT}) €$", s):
                assert cerca(bloque_sum["nominativas"], eur(m[1]))
                filas.append((None, None, None, None, "TOTAL SUBVENCIONES NOMINATIVAS", eur(m[1])))
                continue
            if s == "ALMACEN€":  # el objeto de la Hermandad de Cofradías sigue en la línea de abajo
                f = filas[-1]
                filas[-1] = f[:4] + (f[4] + " ALMACEN",) + f[5:]
                continue
            if m := re.match(rf"^(?:(\d{{4}})\s+)?({AMT}) €$", s):  # subtotal
                assert cerca(suma, eur(m[2])), (s, suma)
                filas.append((None, None, None, None, int(m[1]) if m[1] else None, eur(m[2])))
                suma = 0.0
                continue
            if m := re.match(rf"^(\d{{4}} \d{{3}}\.\d\d)\s+({AMT})\s+(.+)$", s):
                partida, credito, resto = m[1], eur(m[2]), m[3]
                if partida[:4] != prog_actual:  # programa nuevo (algunos no traen fila de subtotal)
                    suma, prog_actual = 0.0, partida[:4]
                if mm := re.match(rf"^(.+?)\s{{2,}}(.+?)\s+({AMT}) ?€?$", resto):  # la partida es también una entidad
                    filas.append((None, partida, credito, mm[1], mm[2], eur(mm[3])))
                    suma += eur(mm[3])
                    bloque_sum[bloque] = bloque_sum.get(bloque, 0) + eur(mm[3])
                    n_ent += 1
                else:
                    filas.append((None, partida, credito, resto))
                continue
            if mm := re.match(rf"^(.+?)\s{{2,}}(.+?)\s+({AMT}) ?€?$", s):
                filas.append((None, None, None, mm[1], mm[2], eur(mm[3])))
                suma += eur(mm[3])
                bloque_sum[bloque] = bloque_sum.get(bloque, 0) + eur(mm[3])
                n_ent += 1
                continue
            if re.fullmatch(r"[A-ZÁÉÍÓÚÑ ]+", s):  # título («TURISMO»)
                filas.append((None, None, None, s))
                continue
            raise AssertionError(f"A12 p.{n}: línea sin reconocer: {l!r}")
    print("A12 entidades:", n_ent, {k: round(v, 2) for k, v in bloque_sum.items()})
    guarda(f"A12 ANEXO SUBVENCIONES NOMINATIVAS {YEAR}.xlsx", str(YEAR), filas)


# ---------------------------------------------------------------- A13.1 (p. 121)
def a13_1():
    filas = [(None, None, None, None, None, None, "ANEXO DE DEUDA"),
             (None, None, None, None, None, None, None, f"PRÉSTAMOS A LARGO PLAZO EN VIGOR A 01/01/{YEAR}"),
             (None, None, "FECHA", "ENTIDAD", "IMPORTE", "PRIMERA AMORTIZ.", "ULTIMA AMORTIZ.", "TIPO DE INTERÉS", "AMORT.",
              "IMPORTE", f"DEUDA VIVA 01/01/{YEAR}", f"AMORTIZ. {YEAR}", f"DEUDA VIVA 31/12/{YEAR}")]
    d = lambda x: datetime.strptime(x, "%d/%m/%Y")
    s_ini = s_am = s_fin = 0.0
    for l in pag(121):
        if m := re.match(rf"^\s*(\d\d/\d\d/\d{{4}})\s+(.+?)\s{{2,}}({AMT})\s+(\d\d/\d\d/\d{{4}})\s+(\d\d/\d\d/\d{{4}})\s+(.+?)\s{{2,}}(CTE\. \w+\.?)\s+({AMT})\s+({AMT})\s+({AMT})\s+({AMT})$", l):
            ini, am, fin = eur(m[9]), eur(m[10]), eur(m[11])
            assert cerca(ini - am, fin), l
            s_ini, s_am, s_fin = s_ini + ini, s_am + am, s_fin + fin
            filas.append((None, None, d(m[1]), m[2], eur(m[3]), d(m[4]), d(m[5]), m[6], m[7], eur(m[8]), ini, am, fin))
        elif m := re.match(rf"^\s+({AMT})\s+({AMT})\s+({AMT})$", l):
            assert cerca(s_ini, eur(m[1])) and cerca(s_am, eur(m[2])) and cerca(s_fin, eur(m[3])), (s_ini, s_am, s_fin)
            filas.append((None,) * 10 + (eur(m[1]), eur(m[2]), eur(m[3])))
        elif "operaciones de tesorería" in l:
            filas.append((None, None, l.strip()))
    assert len(filas) == 3 + 3 + 1 + 1, len(filas)
    print("A13.1 deuda viva 31/12:", round(s_fin, 2))
    guarda("A13.1 Estado de la deuda.xlsx", "AMORTIZACIONES", filas)
    return s_am


# ---------------------------------------------------------------- A13.2 (p. 122-124)
def a13_2(amort):
    filas = [(None, None, f"PREVISIÓN CARGA FINANCIERA {YEAR}")]
    intereses = 0.0
    for n in (122, 123, 124):
        for l in pag(n):
            s = l.strip()
            if not s or "SALINERO" in s or "ONTOSO" in s or "ELIA" in s or "Date:" in s or "by " in s:
                continue
            if m := re.match(rf"^(.*?)\s+({AMT}|\d,\d+%)$", s):
                etiqueta, v = m[1].strip(), m[2]
                valor = round(float(v[:-1].replace(",", ".")) / 100, 6) if v.endswith("%") else eur(v)
                if etiqueta.startswith("INTERESES PRESTAMO"):
                    intereses += valor
                if etiqueta.startswith("TOTAL"):
                    filas.append((None, None, None, None, None, etiqueta, valor))
                else:
                    filas.append((None, etiqueta, None, None, None, None, valor))
            else:
                filas.append((None, s))
    tot = {f[5]: f[6] for f in filas if len(f) > 5 and isinstance(f[5], str)}
    assert cerca(tot[f"TOTAL INTERESES {YEAR}"], intereses), (tot, intereses)
    assert abs(tot[f"TOTAL AMORTIZACIÓN {YEAR}"] - amort) < 0.02
    print("A13.2", tot)
    guarda("A13.2 Carga Financiera.xlsx", "Hoja1", filas)


if __name__ == "__main__":
    gastos, ingresos = a1()
    a2(ingresos)
    a3(gastos)
    a9(gastos[6])
    a12()
    a13_2(a13_1())
