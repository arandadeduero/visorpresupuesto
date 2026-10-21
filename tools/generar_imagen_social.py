#!/usr/bin/env python3
"""Genera las imágenes de site/img/ a partir del escudo oficial (site/img/icon-512.png).

Uso: .venv/bin/python tools/generar_imagen_social.py

Salida (todo en site/img/):
- social.png          1200x630, la imagen que se ve al compartir un enlace (Facebook, X, WhatsApp, LinkedIn, Telegram...)
- escudo.png          escudo recortado para la cabecera (66x99 px; se muestra a 22x33)
- favicon-32.png      icono de pestaña
- apple-touch-icon.png 180x180 sobre fondo blanco (iOS no admite transparencia)
- icon-192.png        192x192 (manifiesto)
Necesita Pillow, fontTools y brotli (requirements.txt); la tipografía Outfit sale de site/fonts/ (woff2 variable).
"""
import io
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
IMG = RAIZ / "site" / "img"
FUENTE = RAIZ / "site" / "fonts" / "outfit-latin-wght-normal.woff2"

# Paleta municipal (la misma que site/css/styles.css)
ROJO, AMBAR, AZUL = "#ce0e2d", "#f5a800", "#0083c1"
GRIS_OSCURO, GRIS, AZUL_CLARO, BLANCO = "#3c3c3c", "#646464", "#e9f4f9", "#ffffff"


def outfit(peso: int, tam: int) -> ImageFont.FreeTypeFont:
    """Outfit variable (woff2) al peso pedido: se pasa a TTF en memoria porque Pillow no lee woff2."""
    ttf = TTFont(FUENTE)
    ttf.flavor = None
    buf = io.BytesIO()
    ttf.save(buf)
    buf.seek(0)
    fuente = ImageFont.truetype(buf, tam)
    fuente.set_variation_by_axes([peso])
    return fuente


def escudo_recortado(origen: Image.Image) -> Image.Image:
    return origen.crop(origen.getchannel("A").getbbox())


def en_cuadrado(escudo: Image.Image, lado: int, margen: float, fondo=None) -> Image.Image:
    util = int(lado * (1 - 2 * margen))
    e = escudo.copy()
    e.thumbnail((util, util), Image.LANCZOS)
    lienzo = Image.new("RGBA", (lado, lado), fondo or (0, 0, 0, 0))
    lienzo.alpha_composite(e, ((lado - e.width) // 2, (lado - e.height) // 2))
    return lienzo


def imagen_social(escudo: Image.Image) -> Image.Image:
    ancho, alto, izq = 1200, 630, 400
    im = Image.new("RGB", (ancho, alto), BLANCO)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, izq, alto), fill=ROJO)
    # Placa clara con el escudo (el escudo no se lee sobre el rojo)
    pw, ph = 270, 400
    px, py = (izq - pw) // 2, (alto - ph) // 2
    d.rounded_rectangle((px, py, px + pw, py + ph), radius=34, fill=BLANCO)
    e = escudo.copy()
    e.thumbnail((pw - 60, ph - 60), Image.LANCZOS)
    im.paste(e, (px + (pw - e.width) // 2, py + (ph - e.height) // 2), e)

    x = izq + 60
    d.text((x, 92), "AYUNTAMIENTO DE ARANDA DE DUERO", font=outfit(600, 24), fill=GRIS)
    titulo = outfit(700, 70)
    d.text((x, 142), "Presupuestos", font=titulo, fill=GRIS_OSCURO)
    d.text((x, 222), "de Aranda de Duero", font=titulo, fill=ROJO)
    lema = outfit(400, 36)
    for i, linea in enumerate(["En qué se gasta tu dinero,", "de dónde sale y qué se debe"]):
        d.text((x, 360 + i * 50), linea, font=lema, fill=GRIS_OSCURO)
    # Tres barras: ámbar, azul y rojo, como el reparto de un presupuesto
    by = 500
    for ancho_b, color in [(250, AMBAR), (170, AZUL), (110, ROJO)]:
        d.rounded_rectangle((x, by, x + ancho_b, by + 16), radius=8, fill=color)
        x += ancho_b + 10
    d.text((izq + 60, 548), "presupuestos.arandadeduero.dev", font=outfit(500, 28), fill=GRIS)
    return im


def main() -> int:
    origen = Image.open(IMG / "icon-512.png").convert("RGBA")
    escudo = escudo_recortado(origen)

    cab = escudo.copy()
    cab.thumbnail((66, 99), Image.LANCZOS)
    cab.save(IMG / "escudo.png", optimize=True)

    en_cuadrado(escudo, 32, 0.04).save(IMG / "favicon-32.png", optimize=True)
    en_cuadrado(escudo, 192, 0.10).save(IMG / "icon-192.png", optimize=True)
    en_cuadrado(escudo, 180, 0.14, fondo=BLANCO).convert("RGB").save(IMG / "apple-touch-icon.png", optimize=True)

    # Cuantizada a una paleta: son colores planos y así pesa muy poco
    imagen_social(escudo).quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(IMG / "social.png", optimize=True)
    for f in ["social.png", "escudo.png", "favicon-32.png", "icon-192.png", "apple-touch-icon.png"]:
        print(f, (IMG / f).stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
