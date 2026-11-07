# Imágenes

## Origen y propiedad

El escudo de Aranda de Duero es propiedad del Ayuntamiento de Aranda de Duero. Se descargó el 21-10-2026 de su web oficial, <https://www.arandadeduero.es/>:

- `icon-512.png`: escudo en color, 512x512, fondo transparente. Origen: `https://www.arandadeduero.es/wp-content/uploads/2026/09/Icono-escudo-Ayto-Aranda-de-Duero-color-512x512-1.png`.

- `logo-ayuntamiento.png`: logotipo horizontal oficial, blanco sobre celeste (`04c-logotipo-horizontal-v1-azul-negativo` de la Imagen Institucional), 720x183. Copiado de `transparencia/assets/logo-horizontal-negativo.webp` del repositorio <https://github.com/arandadeduero/contratos> y pasado a PNG de 16 colores. Va en la franja de la cabecera; su fondo (#30b5e5) es el `--franja` del CSS. No lleva huella en el build (nombre estable).

Todo lo demás de esta carpeta se genera a partir de ese fichero con `tools/generar_imagen_social.py` (ver el README de la raíz):

| Fichero | Para qué | Huella en el build |
|---|---|---|
| `escudo.png` | Escudo del pie (66x99 px, se muestra a 44x66) | Sí |
| `social.png` | Imagen al compartir un enlace (1200x630) | No: URL estable |
| `favicon-32.png` | Icono de pestaña | No |
| `apple-touch-icon.png` | Icono de iOS (180x180, fondo blanco) | No |
| `icon-192.png` | Icono del manifiesto (192x192) | No |
| `icon-512.png` | Icono del manifiesto (512x512) y origen del resto | No |

No tienen huella `social.png` ni los iconos porque los rastreadores de redes sociales y los navegadores los guardan por URL y los piden siempre con el mismo nombre.
