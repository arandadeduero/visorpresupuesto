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
