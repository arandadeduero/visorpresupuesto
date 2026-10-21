#!/usr/bin/env python3
"""Genera site/css/escalas.css: las clases que sustituyen a los estilos en línea.

- .ancho-0 … .ancho-100        width: N %            (barras de las listas)
- .crece-1 … .crece-100        flex-grow: N          (segmentos de las barras divididas)
- --cap-N-tono-K y .cap-N / .cap-N-tono-K   color de un capítulo y de sus tonos (artículos), mezclando
  --cap-N con el destino que indica --tono-K de cada tema (claro u oscuro). No hay literales de color.

Uso: python3 tools/generar_escalas.py          (escribe el fichero)
     python3 tools/generar_escalas.py --check  (falla si el fichero no está al día)
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "site" / "css" / "escalas.css"
CAPITULOS = range(1, 10)
TONOS = range(0, 6)  # 0 = el color del capítulo; 1-5 se definen en --tono-K de styles.css


def generar() -> str:
    L = [
        "/* GENERADO por tools/generar_escalas.py: no editar a mano (un test comprueba que está al día). */",
        "/* Tonos de capítulo: --cap-N-tono-K (K = 0 es el color del capítulo; K >= 1 lo mezcla según --tono-K del tema). */",
        ":root {",
    ]
    for n in CAPITULOS:
        L.append(f"  --cap-{n}-tono-0: var(--cap-{n});")
        for k in range(1, 6):
            L.append(f"  --cap-{n}-tono-{k}: color-mix(in srgb, var(--cap-{n}), var(--tono-{k}));")
    L.append("}")
    L.append("")
    L.append("/* Color por capítulo y tono (--color lo leen .muestra, .punto, .seg…) */")
    for n in CAPITULOS:
        L.append(f".cap-{n} {{ --color: var(--cap-{n}); }}")
        for k in range(1, 6):
            L.append(f".cap-{n}-tono-{k} {{ --color: var(--cap-{n}-tono-{k}); }}")
    L.append("")
    L.append("/* Anchos (% redondeado) */")
    for n in range(0, 101):
        L.append(f".ancho-{n} {{ width: {n}%; }}")
    L.append("")
    L.append("/* Proporciones de las barras divididas (flex-grow, % redondeado; mínimo 1 para que todo lo que existe se vea) */")
    for n in range(1, 101):
        L.append(f".crece-{n} {{ flex-grow: {n}; }}")
    return "\n".join(L) + "\n"


def main(argv):
    texto = generar()
    if "--check" in argv:
        if not SALIDA.exists() or SALIDA.read_text(encoding="utf-8") != texto:
            print(f"{SALIDA} no está al día: ejecuta python3 tools/generar_escalas.py", file=sys.stderr)
            return 1
        return 0
    SALIDA.write_text(texto, encoding="utf-8")
    print(f"escrito {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
