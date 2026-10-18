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
