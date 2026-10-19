"""Traducciones y agrupaciones en lenguaje llano: (nombre corto, nombre oficial)."""

CAPITULOS_GASTOS = {
    1: ("Personal", "Gastos de personal"),
    2: ("Servicios y mantenimiento", "Gastos corrientes en bienes y servicios"),
    3: ("Intereses de préstamos", "Gastos financieros"),
    4: ("Ayudas y transferencias", "Transferencias corrientes"),
    5: ("Fondo de imprevistos", "Fondo de contingencia"),
    6: ("Obras e inversiones", "Inversiones reales"),
    7: ("Ayudas para inversiones", "Transferencias de capital"),
    8: ("Activos financieros", "Activos financieros"),
    9: ("Devolución de préstamos", "Pasivos financieros"),
}

CAPITULOS_INGRESOS = {
    1: ("Impuestos directos (IBI, IAE, vehículos…)", "Impuestos directos"),
    2: ("Impuestos indirectos (obras)", "Impuestos indirectos"),
    3: ("Tasas y precios públicos", "Tasas y otros ingresos"),
    4: ("Transferencias de otras administraciones", "Transferencias corrientes"),
    5: ("Ingresos de patrimonio", "Ingresos patrimoniales"),
    6: ("Venta de inversiones", "Enajenación de inversiones reales"),
    7: ("Subvenciones para obras", "Transferencias de capital"),
    8: ("Activos financieros", "Activos financieros"),
    9: ("Préstamos", "Pasivos financieros"),
}

# Artículos (dos primeros dígitos del código económico): código → (nombre, nombre oficial).
# Fuente de los nombres oficiales: clasificación económica del Anexo III (gastos) y IV (ingresos) de la Orden EHA/3565/2008,
# de 3 de diciembre, por la que se aprueba la estructura de los presupuestos de las entidades locales (BOE n.º 297,
# de 10-12-2008, https://www.boe.es/buscar/act.php?id=BOE-A-2008-19916), con las modificaciones de la Orden HAP/419/2014
# (BOE n.º 67, de 19-03-2014, https://www.boe.es/buscar/act.php?id=BOE-A-2014-2922): crea el capítulo 5 (artículo 50) y
# suprime el artículo 27. El nombre es una versión corta y llana; el oficial va tal cual, sin punto final. Si el oficial
# solo tiene sentido dentro de su capítulo («De la Administración del Estado»), el nombre lo completa.
ARTICULOS_INGRESOS = {
    "11": ("Impuestos sobre el capital", "Impuestos sobre el capital"),
    "13": ("Impuesto sobre actividades económicas", "Impuesto sobre las Actividades Económicas"),
    "29": ("Otros impuestos indirectos", "Otros impuestos indirectos"),
    "30": ("Tasas por servicios públicos básicos", "Tasas por la prestación de servicios públicos básicos"),
    "32": ("Tasas por actividades de competencia local", "Tasas por la realización de actividades de competencia local"),
    "33": ("Tasas por usar el dominio público", "Tasas por la utilización privativa o el aprovechamiento especial del dominio público"),
    "34": ("Precios públicos", "Precios públicos"),
    "35": ("Contribuciones especiales", "Contribuciones especiales"),
    "36": ("Ventas", "Ventas"),
    "38": ("Reintegros de operaciones corrientes", "Reintegros de operaciones corrientes"),
    "39": ("Otros ingresos", "Otros ingresos"),
    "42": ("Transferencias de la Administración del Estado", "De la Administración del Estado"),
    "45": ("Transferencias de Comunidades Autónomas", "De Comunidades Autónomas"),
    "46": ("Transferencias de entidades locales", "De Entidades Locales"),
    "47": ("Transferencias de empresas privadas", "De Empresas privadas"),
    "49": ("Transferencias del exterior", "Del exterior"),
    "52": ("Intereses de depósitos", "Intereses de depósitos"),
    "54": ("Rentas de bienes inmuebles", "Rentas de bienes inmuebles"),
    "55": ("Concesiones y aprovechamientos especiales", "Productos de concesiones y aprovechamientos especiales"),
    "59": ("Otros ingresos patrimoniales", "Otros ingresos patrimoniales"),
    "60": ("Venta de terrenos", "De terrenos"),
    "75": ("Subvenciones de Comunidades Autónomas", "De Comunidades Autónomas"),
    "78": ("Subvenciones de familias e instituciones sin fines de lucro", "De familias e instituciones sin fines de lucro"),
    "79": ("Subvenciones del exterior", "Del exterior"),
    "83": ("Reintegros de préstamos concedidos fuera del sector público", "Reintegros de préstamos de fuera del sector público"),
    "87": ("Remanente de tesorería", "Remanente de tesorería"),
    "91": ("Préstamos recibidos", "Préstamos recibidos en euros"),
}

ARTICULOS_GASTOS = {
    "10": ("Órganos de gobierno y personal directivo", "Órganos de gobierno y personal directivo"),
    "11": ("Personal eventual", "Personal eventual"),
    "12": ("Personal funcionario", "Personal Funcionario"),
    "13": ("Personal laboral", "Personal Laboral"),
    "15": ("Incentivos al rendimiento", "Incentivos al rendimiento"),
    "16": ("Cuotas y gastos sociales a cargo del empleador", "Cuotas, prestaciones y gastos sociales a cargo del empleador"),
    "20": ("Arrendamientos y cánones", "Arrendamientos y cánones"),
    "21": ("Reparaciones, mantenimiento y conservación", "Reparaciones, mantenimiento y conservación"),
    "22": ("Material, suministros y otros", "Material, suministros y otros"),
    "23": ("Indemnizaciones por razón del servicio", "Indemnizaciones por razón del servicio"),
    # El artículo 27 («Gastos imprevistos y funciones no clasificadas») lo suprimió la Orden HAP/419/2014, pero el Excel
    # de 2026 sigue usando el código 277 para un contrato. Nombre neutro, a partir de su capítulo.
    "27": ("Otros gastos en bienes y servicios", "Artículo 27, «Gastos imprevistos y funciones no clasificadas», suprimido por la Orden HAP/419/2014; el Ayuntamiento conserva el código"),
    "31": ("Intereses de préstamos", "De préstamos y otras operaciones financieras en euros"),
    "35": ("Intereses de demora y otros gastos financieros", "Intereses de demora y otros gastos financieros"),
    "46": ("Transferencias a entidades locales", "A Entidades Locales"),
    "47": ("Transferencias a empresas privadas", "A Empresas privadas"),
    "48": ("Transferencias a familias e instituciones sin fines de lucro", "A Familias e Instituciones sin fines de lucro"),
    "50": ("Fondo de contingencia", "Dotación al Fondo de Contingencia de Ejecución Presupuestaria"),
    "60": ("Inversión nueva en infraestructuras y bienes de uso general", "Inversión nueva en infraestructuras y bienes destinados al uso general"),
    "61": ("Reposición de infraestructuras y bienes de uso general", "Inversiones de reposición de infraestructuras y bienes destinados al uso general"),
    "62": ("Inversión nueva para el funcionamiento de los servicios", "Inversión nueva asociada al funcionamiento operativo de los servicios"),
    "63": ("Reposición para el funcionamiento de los servicios", "Inversión de reposición asociada al funcionamiento operativo de los servicios"),
    "64": ("Inversiones inmateriales", "Gastos en inversiones de carácter inmaterial"),
    "65": ("Inversiones gestionadas para otros entes públicos", "Inversiones gestionadas para otros entes públicos"),
    "68": ("Inversiones en bienes patrimoniales", "Gastos en inversiones de bienes patrimoniales"),
    "78": ("Ayudas para inversiones a familias e instituciones sin fines de lucro", "A familias e instituciones sin fines de lucro"),
    "83": ("Préstamos concedidos fuera del sector público", "Concesión de préstamos fuera del sector público"),
    "91": ("Devolución de préstamos", "Amortización de préstamos y de operaciones en euros"),
}


def articulo_ingresos(codigo: str) -> tuple[str, str]:
    return ARTICULOS_INGRESOS.get(codigo, (f"Artículo {codigo}", f"Artículo {codigo}"))


def articulo_gastos(codigo: str) -> tuple[str, str]:
    return ARTICULOS_GASTOS.get(codigo, (f"Artículo {codigo}", f"Artículo {codigo}"))


AREAS = {
    0: "Deuda",
    1: "Servicios básicos (seguridad, limpieza, urbanismo…)",
    2: "Protección social",
    3: "Sanidad, educación, cultura y deporte",
    4: "Economía y empleo",
    9: "Administración general",
}

BLOQUES_100 = [
    ("Obras e inversiones", [6, 7]),
    ("Servicios", [2]),
    ("Personal", [1]),
    ("Otros", [3, 4, 5, 8, 9]),
]

# Políticas de gasto (primeros dos dígitos del programa) según la clasificación por programas oficial
# (Orden EHA/3565/2008), con su nombre oficial, que ya es llano para el vecino.
POLITICAS = {
    "01": "Deuda pública",
    "13": "Seguridad y movilidad ciudadana",
    "15": "Vivienda y urbanismo",
    "16": "Bienestar comunitario",
    "17": "Medio ambiente",
    "22": "Otras prestaciones económicas",
    "23": "Servicios sociales y promoción social",
    "24": "Fomento del empleo",
    "31": "Sanidad",
    "32": "Educación",
    "33": "Cultura",
    "34": "Deporte",
    "42": "Industria y energía",
    "43": "Comercio, turismo y pequeñas y medianas empresas",
    "44": "Transporte público",
    "45": "Infraestructuras",
    "46": "Investigación, desarrollo e innovación",
    "49": "Otras actuaciones de carácter económico",
    "91": "Órganos de gobierno",
    "92": "Servicios de carácter general",
    "93": "Administración financiera y tributaria",
    "94": "Transferencias a otras administraciones públicas",
}

# Población para los importes «por habitante»: año del presupuesto → (habitantes, año del dato, fuente).
# Para un año sin dato propio del INE se usa el último disponible (es el caso de 2026, que usa el de 2025).
POBLACION = {
    2024: (33757, 2024, "INE (población de Aranda de Duero en 2024), consultada en Gobierto Presupuestos"),
    2025: (33956, 2025, "INE (población de Aranda de Duero en 2025), consultada en Gobierto Presupuestos"),
    2026: (33956, 2025, "INE (población de Aranda de Duero en 2025), consultada en Gobierto Presupuestos"),
}
