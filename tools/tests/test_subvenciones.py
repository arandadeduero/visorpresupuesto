import openpyxl
import pytest

from budget.common import find_file
from budget.subvenciones import parse_subvenciones

ANIOS = [2024, 2025, 2026]


@pytest.fixture(scope="module", params=ANIOS)
def caso(request):
    return request.param, parse_subvenciones(request.param)


def programa(d, partida):
    return next(p for p in d["programas"] if p["partida"] == partida)


def item(p, entidad):
    return next(i for i in p["items"] if i["entidad"] == entidad)


def filas_del_excel(anio):
    ws = openpyxl.load_workbook(find_file(anio, "A12"), data_only=True)[str(anio)]
    return [tuple(f) + (None,) * 8 for f in ws.iter_rows(values_only=True)]


def subtotales_del_excel(anio):
    """Filas de subtotal por programa del propio Excel (código en la columna E y las sumas en F y G), por bloque."""
    out = {}
    bloque = "nominativas"
    for fila in filas_del_excel(anio):
        if isinstance(fila[3], str) and fila[3].startswith("APORTACIONES Y CUOTAS"):
            bloque = "cuotas"
        if fila[1] is None and fila[3] is None and isinstance(fila[4], (int, float)) and isinstance(fila[5], (int, float)):
            out[(bloque, str(int(fila[4])))] = (fila[5], fila[6] or 0)
    return out


def test_los_subtotales_de_cada_programa_coinciden_con_los_del_excel(caso):
    anio, d = caso
    esperado = subtotales_del_excel(anio)
    assert esperado, "no se han leído subtotales del Excel"
    obtenido = {(p["bloque"], p["codigo"]): p["actual"] for p in d["programas"]}
    # los programas de una sola entidad (1610, 1710, 3341…) no llevan fila de subtotal en el Excel
    assert set(esperado) <= set(obtenido)
    # Solo se compara el año del presupuesto: el subtotal del año anterior del Excel no siempre suma sus filas (p. ej. «3373» en 2025).
    for clave, (_, act) in esperado.items():
        assert obtenido[clave] == pytest.approx(act, abs=0.01), clave


def test_el_total_de_las_nominativas_coincide_con_la_fila_total_del_excel(caso):
    # «TOTAL SUBVENCIONES NOMINATIVAS»: 752.250 (2024), 681.600 (2025) y 689.100 (2026). En el Excel de 2024 esa celda es
    # 95.000 € menor que la suma de los subtotales de sus programas (847.250 €, que sí coinciden uno a uno con el Excel):
    # los 95.000 € de «Concurrencia competitiva» que figuran en la columna I de los programas 3373 y 4320.
    anio, d = caso
    fila = next(f for f in filas_del_excel(anio) if isinstance(f[4], str) and f[4].startswith("TOTAL SUBVENCIONES"))
    noms = sum(p["actual"] for p in d["programas"] if p["bloque"] == "nominativas")
    assert noms == pytest.approx(fila[6] + (95000 if anio == 2024 else 0), abs=0.01)


def test_cada_programa_tiene_un_identificador_unico_y_las_cuotas_van_aparte(caso):
    _, d = caso
    claves = [(p["bloque"], p["codigo"]) for p in d["programas"]]
    assert len(claves) == len(set(claves))
    assert {p["bloque"] for p in d["programas"]} == {"nominativas", "cuotas"}


def test_las_filas_de_titulo_y_de_cabecera_no_son_entidades(caso):
    _, d = caso
    nombres = {i["entidad"].lower() for p in d["programas"] for i in p["items"]}
    assert not nombres & {"turismo", "desarrollo económico", "desarrollo economico", "programa", "entidad beneficiaria"}
    assert not any(e["entidad"].lower() == "turismo" for e in d["entidades"])


def test_programas_donde_la_partida_es_tambien_la_primera_entidad(caso):
    # «4330 479.00» (Sonorama, 145.200 € en 2025 y 2026) y «4330 489.00» (ASOHAR) llevan importes en la propia fila de la partida.
    anio, d = caso
    desarrollo = next(p for p in d["programas"] if p["bloque"] == "nominativas" and p["codigo"] == "4330")
    assert desarrollo["programa"] == "Desarrollo económico"
    nombres = {i["entidad"].strip(): i for i in desarrollo["items"]}
    if anio >= 2025:
        assert nombres["Sonorama Producciones SL"]["actual"] == 145200
        assert nombres["ASOHAR"]["objeto"] == "Plan dinamización hostelería"
    turismo = next(p for p in d["programas"] if p["bloque"] == "cuotas" and p["codigo"] == "4320")
    assert turismo["programa"] == "Turismo"
    nombres = [i["entidad"].lower() for i in turismo["items"]]
    assert "consorcio ruta del vino ribera del duero" in nombres
    assert any("museos del vino" in n for n in nombres)


def test_totales_coherentes(caso):
    _, d = caso
    assert d["total"] > 0
    assert d["total"] == pytest.approx(sum(p["actual"] for p in d["programas"]), abs=0.01)
    assert d["total"] == pytest.approx(sum(e["actual"] for e in d["entidades"]), abs=0.01)
    assert d["totalAnterior"] == pytest.approx(sum(e["anterior"] for e in d["entidades"]), abs=0.01)


def test_totales_de_cada_anio():
    esperado = {2024: (822007.1, 898237.1), 2025: (530637.1, 730937.1), 2026: (694937.1, 738437.1)}
    for anio, (anterior, actual) in esperado.items():
        d = parse_subvenciones(anio)
        assert (d["totalAnterior"], d["total"]) == pytest.approx((anterior, actual), abs=0.01), anio


def test_entidades_agrupadas_sin_tildes_ni_mayusculas(caso):
    _, d = caso
    nombres = [e["entidad"] for e in d["entidades"]]
    assert all(n.strip() for n in nombres)
    claves = [n.lower() for n in nombres]
    assert len(claves) == len(set(claves))
    cruz = next(e for e in d["entidades"] if e["entidad"] == "Cruz Roja")
    assert "Asistencia social primaria" in cruz["programas"]


def test_el_credito_de_la_partida_puede_faltar_pero_nunca_es_un_texto(caso):
    # En el Excel de 2025 el crédito de cada partida es el texto «Loading...»: queda como null.
    anio, d = caso
    assert all(p["credito"] is None or isinstance(p["credito"], float) for p in d["programas"])
    if anio == 2025:
        assert all(p["credito"] is None for p in d["programas"])
    else:
        assert programa(d, "2311 489.00")["credito"] > 0


def test_cruz_roja_en_asistencia_social_cada_anio():
    esperado = {2024: (8460, 8500), 2025: (8500, 10000), 2026: (10000, 10000)}
    for anio, (anterior, actual) in esperado.items():
        p = programa(parse_subvenciones(anio), "2311 489.00")
        assert p["programa"] == "Asistencia social primaria"
        cruz = item(p, "Cruz Roja")
        assert (cruz["anterior"], cruz["actual"]) == (anterior, actual), anio
        assert cruz["objeto"].startswith("Actividades sociales")
    assert item(programa(parse_subvenciones(2026), "2311 489.00"), "Cáritas")["actual"] == 3000
    assert item(programa(parse_subvenciones(2025), "2311 489.00"), "Cáritas")["actual"] == 10000


def test_entidad_en_programa_pequeno(caso):
    _, d = caso
    assert item(programa(d, "1700 489.00"), "Club Deportivo Espeleoduero")["actual"] == 2000


def test_2024_los_nombres_en_mayusculas_del_excel_se_pasan_a_frase_normal():
    d = parse_subvenciones(2024)
    nombres = [i["entidad"] for p in d["programas"] for i in p["items"]]
    assert "Asoc. Española de Lucha contra el Cancer" in nombres
    assert "CRUZ ROJA" not in nombres
    # una sola palabra se deja tal cual, por si es una sigla
    assert "AFAR" in nombres
