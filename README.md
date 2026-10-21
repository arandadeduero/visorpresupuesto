# Presupuestos de Aranda de Duero

**🌐 Web: <https://presupuestos.arandadeduero.dev/>**

Visor de los presupuestos del Ayuntamiento de Aranda de Duero pensado para cualquier vecino, sin necesidad de saber de presupuestos: en qué se gasta el dinero, de dónde sale, qué obras se prevén, a quién se dan subvenciones y cuánto se debe.

Incluye los **presupuestos aprobados 2024, 2025 y 2026** (previsiones, no gastos ya realizados); por defecto se muestra el último y hay un selector de año.

## Qué se puede ver

| Página | Qué responde |
|---|---|
| **Inicio** | «Por cada 100 € que gasta el Ayuntamiento…», euros por habitante y una tarjeta «¿Cuánto gasta Aranda de Duero en…?» |
| **Resumen** | Ingresos frente a gastos, gráficos de quesito (por capítulos o por artículos) y qué ha cambiado más respecto al año anterior |
| **Ingresos** | De dónde sale el dinero: capítulo → artículo → concepto, con buscador |
| **Gastos** | En qué se gasta, por política (cultura, deporte…) o por tipo de gasto (capítulo → artículo → partida; el personal se queda en el artículo) |
| **Inversiones** | Obras y compras previstas y cómo se financia cada una |
| **Subvenciones** | A qué entidades se da dinero, por actividad y por entidad |
| **Deuda** | Préstamos actuales, deuda por año, coste anual y la previsión de un préstamo nuevo |
| **Indicadores** | Ahorro bruto y neto, nivel de endeudamiento (frente a los umbrales legales del 75 % y el 110 %), deuda por habitante, impuestos y tasas por habitante… |
| **Comparar** | Dos presupuestos a elegir, frente a frente: barras pareadas por política o capítulo, tabla, frases, indicadores, por habitante y evolución |
| **Calculadora** | «¿A qué se destina lo que pago?»: reparto orientativo de tus impuestos y tasas |
| **Guía** | Qué significan las palabras del presupuesto |
| **Descargas** | Los datos en JSON y los Excel originales |

Todas las tablas se pueden ordenar pulsando su cabecera (y arrancan ordenadas por la primera columna).

Los gráficos usan los colores del Ayuntamiento, la web funciona bien en el móvil y todo importe procede de los Excel oficiales (no se inventa ningún dato).

**Capítulos y artículos.** Los quesitos de Resumen, Ingresos y Gastos se ven por defecto por **capítulos** (los 9 grandes bloques) y tienen un selector «Ver por: Capítulos | Artículos». El **artículo** es el siguiente nivel de la clasificación económica (los dos primeros dígitos del código: 91 «Préstamos recibidos», 29 «Otros impuestos indirectos», 12 «Personal funcionario»). Los nombres oficiales vienen de la Orden EHA/3565/2008 (BOE de 10-12-2008) y de la Orden HAP/419/2014; las fuentes están en `tools/budget/labels.py`.

## Cómo funciona

- `2024/`, `2025/` y `2026/` contienen los Excel oficiales de cada presupuesto.
- `tools/` convierte esos Excel en ficheros JSON (Python con `openpyxl`) y avisa si algún total no cuadra.
- `site/` es la web: HTML y JavaScript simples, sin framework, sin servidor. Lee los JSON de `site/data/` y dibuja los gráficos con [Chart.js](https://www.chartjs.org/), guardado en `site/vendor/` (no depende de ningún CDN).
- GitHub Actions publica solo la carpeta `site/` en GitHub Pages.
- El diseño y el plan de construcción están en `docs/superpowers/`.

## Previsualizar en local

```bash
python3 -m http.server -d site 8000
# abrir http://localhost:8000
```

(No sirve abrir los ficheros con doble clic: el navegador bloquea la carga de datos.)

## Regenerar los datos

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python tools/convert.py 2024   # o 2025, 2026
```

## Añadir otro año

1. Crear la carpeta `AAAA/` con los mismos Excel (nombres que empiezan por `A1`, `A2`, `A3`, `A9`, `A12`, `A13.1` y `A13.2`).
   **Cada Excel debe llevar una sola hoja** (la del ejercicio: sin copias, borradores ni hojas de trabajo); un test lo comprueba.
2. Añadir la población de ese año en `tools/budget/labels.py` (`POBLACION`).
3. `.venv/bin/python tools/convert.py AAAA`
4. Revisar los avisos, hacer commit de `site/data/` y publicar.

El selector de año de la web lee `site/data/index.json`, que el script actualiza solo.

**Claves de los JSON.** Son las mismas en todos los años: `actual` es el importe del año del presupuesto y `anterior` el del año anterior (`anterior2` el de hace dos años en ingresos, solo si el Excel lo trae). `total`/`totalAnterior` en subvenciones y `totalGastosAnterior` en el resumen siguen la misma idea. El conversor localiza las columnas por sus rótulos, no por su posición, porque cambian de un ejercicio a otro.

**Artículos en los JSON.** `ingresos.json`: cada capítulo trae `articulos` y cada concepto su `articulo`. `gastos.json`: `articulos` (lista plana con `cap`) y cada partida su `articulo` (el capítulo 1 sigue agrupado por programa, sin `articulo`, pero sus artículos sí están en `articulos`).

**Diferencias entre ejercicios** (detalle en el documento de diseño): 2024 no tiene préstamo previsto en el anexo de deuda (`previsto`, `vivaFinConPrevisto` e `interesesConPrevisto` valen `null` y la web no muestra esas cajas); en 2025 el Excel trae 250.000 € más de ingresos que de gastos (es una nota, no un aviso); en 2024 y 2025 el Excel de gastos no trae las inversiones del año anterior, así que esas partidas, programas y políticas quedan sin variación (`null`, `sinAnterior`).

## Tests

```bash
.venv/bin/pytest                      # conversor y comprobaciones de la web, con los Excel reales
node --test "site/js/*.test.js"       # formato, búsqueda, árbol de gastos, indicadores y calculadora
```

## Tema claro y oscuro, variables CSS y sin estilos en línea

- **Sigue al sistema.** `:root { color-scheme: light dark }` y un bloque `@media (prefers-color-scheme: dark)` que redefine los tokens: la web se ve en claro u oscuro según el sistema del visitante y cambia en vivo si éste lo cambia (los gráficos se repintan sin recargar). No hay interruptor manual (decisión: manda el sistema). Cada HTML lleva dos `<meta name="theme-color">` con `media` (rojo municipal en claro, rojo oscuro en oscuro).
- **Todos los colores son variables.** En `site/css/styles.css`, los únicos literales de color están en los bloques `:root`: primero la paleta municipal (`--rojo`, `--ambar`, `--marron`, `--azul`, `--azul-claro`, `--gris`, `--gris-oscuro`, `--celeste`, `--azul-cielo`, `--ambar-claro`…), luego los tokens semánticos (`--fondo`, `--fondo-suave`, `--superficie`, `--texto`, `--texto-suave`, `--borde`, `--enlace`, `--cabecera-*`, `--aviso-*`, `--error-*`, `--foco`, `--sombra`, `--grafico-*`, `--tooltip-*`, `--serie-N`, `--cap-N`, `--tono-K`…). El resto del CSS solo usa `var(--…)` y `color-mix()`. Para cambiar un color hay que tocar un único sitio.
- **Oscuro:** fondo `#14181c`, superficie `#1d2329`, superficie suave `#252d35`, texto `#e7ebee`, enlaces `#5bbae8`, cabecera en rojo oscuro `#8f0a20`, foco ámbar, acentos y colores de capítulo aclarados para ≥ 3:1 sobre la superficie, y tonos de artículo solo más claros.
- **Sin estilos en línea.** Ningún `style=` en los HTML ni en las plantillas de los módulos, y ningún `element.style`. Las anchuras y proporciones son clases (`.ancho-0…100`, `.crece-1…100`) y los colores también (`.serie-N`, `.cap-N`, `.cap-N-tono-K`). `site/css/escalas.css` se **genera** con `python3 tools/generar_escalas.py` (no editar a mano; un test comprueba que está al día).
- **Colores en los gráficos.** `site/js/colores.js` lee las variables con `getComputedStyle` (`colorVar('--cap-1')`); `charts.js` las usa como opciones «scriptable» de Chart.js y repinta todos los gráficos cuando cambia `prefers-color-scheme`.
- **Content-Security-Policy** por `<meta>` en cada página: `default-src 'self'; script-src 'self' https://www.googletagmanager.com; style-src 'self'; …`, sin `unsafe-inline` (Google solo tras el consentimiento: ver «Analítica y privacidad»). Por eso el aviso de `file://` es un fichero (`js/aviso-file.js`) y no un script en línea. Chart.js solo modifica `canvas.style` por CSSOM, que la política permite (comprobado: sin violaciones en consola).
- Tests: `tools/tests/test_estilos.py` (sin literales de color fuera de `:root`, sin `style=`, CSP, escalas al día) y `site/js/tema.test.js` (contraste AA de los pares texto/fondo reales en los dos temas).

## Logo, redes sociales e iconos

- **Logo.** El escudo oficial (propiedad del Ayuntamiento; origen y fecha en `site/img/README.md`) va en la cabecera, dentro del enlace a la portada, junto al título. Se muestra sobre una **placa clara** (`--logo-placa`) en los dos temas: el escudo tiene colores propios (rojo, ámbar, azul) y no se lee directamente sobre el rojo de la cabecera; el banner oficial con texto gris oscuro tampoco. `<img>` con `alt="Ayuntamiento de Aranda de Duero"`, `width`/`height` (22x33, imagen de 66x99 para pantallas 2x) y estilos solo en CSS. La cabecera mide lo mismo que antes (45 px). `layout.js` lee la ruta con huella de `<html data-escudo>`, que pone el build.
- **Etiquetas en cada HTML.** `description`, `canonical` (URL absoluta), Open Graph (`og:type`, `site_name`, `locale`, `title`, `description`, `url`, `image` y su ancho, alto, tipo y `alt`; lo usan Facebook, Instagram al compartir enlace, WhatsApp, LinkedIn, Telegram...) y Twitter/X (`twitter:card=summary_large_image`, `title`, `description`, `image`, `image:alt`). Títulos y descripciones únicos y sin cifras. Además: `icon` (PNG 32), `apple-touch-icon` (180), `manifest.webmanifest` (iconos 192 y 512), `robots.txt` y `sitemap.xml` (ver «URLs propias por año»). La CSP no cambia.
- **URLs estables.** `img/social.png`, los iconos, el manifiesto, `robots.txt` y `sitemap.xml` no llevan huella (los rastreadores y navegadores los piden por nombre); solo `img/escudo.png` la lleva.
- **Regenerar las imágenes** (a partir de `site/img/icon-512.png`, con Outfit de `site/fonts/`):

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/python tools/generar_imagen_social.py
```

  La imagen social (1200x630, unos 25 KB) tiene a la izquierda un panel rojo con el escudo sobre una placa blanca y a la derecha «Presupuestos de Aranda de Duero», el lema «En qué se gasta tu dinero, de dónde sale y qué se debe», tres barras ámbar, azul y roja y la dirección web.
- **Probar** tras publicar: [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) (sirve también para Instagram y WhatsApp), [LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/) y, para X, el borrador de un post (el validador de tarjetas ya no existe). Si cambia la imagen, usar «Scrape again» en Facebook: las redes la guardan por URL.
- Tests: `tools/tests/test_social.py`.

## Analítica y privacidad

- **Qué se mide.** Google Analytics 4 (ID `G-BXMC22W46S`, el mismo medidor compartido con las webs de fiestas y bienestar animal del Ayuntamiento): visitas a páginas (`page_view`) y los datos que envía por defecto `gtag.js`. No se envía ningún dato propio de la persona ni del presupuesto consultado.
- **Consentimiento previo.** No se carga ni se envía nada a Google hasta que se pulsa «Aceptar» en el aviso que sale abajo en todas las páginas (lo monta `site/js/layout.js` llamando a `iniciarAnalitica()` de `site/js/analytics.js`). «Aceptar» se recuerda (`localStorage`, clave `presupuestosAranda:analytics-consent`, valor `{v,t}`). «Rechazar» no instala nada y caduca a los 4 días, cuando se vuelve a preguntar. Valores corruptos o con fecha futura: se pregunta. Sin `localStorage` no se recuerda nada y Google nunca carga sin «Aceptar».
- **Preferencias.** El enlace «Preferencias de analítica» del pie borra la decisión, desactiva el seguimiento (`window['ga-disable-<ID>']`), borra las cookies `_ga*` (en el host y los dominios superiores) y vuelve a preguntar, con el foco en «Aceptar».
- **Do Not Track.** Con DNT activado no hay aviso, ni Google, ni enlace de preferencias.
- **Un solo sitio de configuración:** `site/js/analytics-config.js` (ID, clave, caducidad del rechazo y URL de la política de privacidad del Ayuntamiento). **Para desactivar la analítica** basta quitar la llamada a `iniciarAnalitica()` de `layout.js` (y la CSP, si se quiere); **para cambiar de medidor**, el ID de ese fichero. Un test impide que el ID aparezca en otro sitio.
- **CSP.** La política permite `https://www.googletagmanager.com` en `script-src`, `https://*.google-analytics.com https://*.googletagmanager.com` en `img-src` y esos dos más `https://*.analytics.google.com` en `connect-src` (sin `unsafe-inline` ni `unsafe-eval`, `style-src 'self'` intacto). El navegador permite esos dominios en todo momento, pero el código solo los carga si hay consentimiento; `tools/tests/test_analitica.py` comprueba que ningún HTML ni otro módulo los nombra ni carga scripts de Google y que la CSP es idéntica en las 12 páginas. Si en el futuro se activaran funciones de publicidad de Google, habría que ampliar la CSP (p. ej. `doubleclick.net`).
- **Cómo probarla.** `python3 -m http.server -d site 8000`; con las herramientas de red del navegador comprobar que sin pulsar nada no hay peticiones a Google, que «Rechazar» tampoco, y que «Aceptar» pide `gtag/js?id=G-BXMC22W46S`. Para repetir: borrar la clave de `localStorage` o pulsar «Preferencias». Tests: `site/js/analytics.test.js` (estado del consentimiento, DNT, cookies, ID único) y `tools/tests/test_analitica.py`.
- **Revisión legal pendiente con el Ayuntamiento:** que su política de privacidad mencione Google Analytics y estas cookies (`_ga`, `_ga_*`) y esta web, y la transferencia de datos a Google.

## Publicación y comprobaciones automáticas

- **En cada Pull Request** (`.github/workflows/ci.yml`): `pytest`, comprobación de que los JSON de `site/data/` están al día y cuadran con los Excel, tests de JavaScript y construcción de `dist/` con sus comprobaciones.
- **En cada push a `main`** (`.github/workflows/pages.yml`): se repiten los tests y, solo si pasan, se construye `dist/` (ver «Despliegue con huellas») y se publica en GitHub Pages. Al final, el propio workflow comprueba, con los nombres del manifiesto, que la web publicada carga.
- La web se sirve en <https://presupuestos.arandadeduero.dev/> (dominio configurado en *Settings → Pages*, con origen «GitHub Actions»).

## URLs propias por año

Cada presupuesto tiene sus páginas indexables: «presupuesto Aranda de Duero 2025» tiene su URL, `/2025/`, y el gasto de ese año `/2025/gastos.html`. Los años salen de `site/data/index.json`; no hay ninguno escrito a mano.

**Estructura de `dist/`** (`tools/build_site.py`):

- `/<año>/` (portada, «por cada 100 €») y `/<año>/resumen.html`, `ingresos`, `gastos`, `inversiones`, `subvenciones`, `deuda`, `indicadores`, `calculadora`: 9 páginas por año (27 con 2024, 2025 y 2026). Salen de los mismos `site/*.html`, un nivel por debajo de la raíz, con los datos del año en el HTML estático.
- En la raíz: `/` (portada del último año y bloque «Presupuestos por año» con un enlace a cada uno), las páginas que no dependen del año (`comparar.html` con `?a=&b=`, `guia.html`, `metodologia.html`, `descargas.html`) y **alias del último año** (`/gastos.html`, `/resumen.html`...) para no romper enlaces antiguos ni los compartidos en redes. Con 3 años, `dist/` tiene 41 HTML (27 + 13 + `404.html`).
- Cuando llegue un año nuevo solo cambia qué año es el último (`index.json`): el build lo calcula, sin tocar código.

**Canonical** (una sola página indexable por contenido): `/` → `/`; `/2026/` (último año) → `/`; `/2025/` y `/2024/` → ellas mismas; `/2026/gastos.html` → ella misma; el alias `/gastos.html` → `/2026/gastos.html`; páginas sin año → ellas mismas. `sitemap.xml` lista solo las páginas cuya canónica es ella misma (31 URLs), con `lastmod` por año (el mayor entre el último commit de `site/data/<año>` y el del resto de `site/`).

**SEO de cada año** (`tools/seo.py`): título ≤ 60 y descripción 120–160 únicos con el año y sin cifras («Gastos del Ayuntamiento de Aranda de Duero en 2025»), Open Graph/Twitter con `og:url` y título del año, `BreadcrumbList` Inicio › Presupuesto 2025 › Gastos, prerender con los JSON de ese año, «Relacionado» con enlaces del mismo año y «Otros años» (la misma página en los demás, con anclas descriptivas). `descargas` sigue con un `Dataset` por año.

**Rutas con profundidad.** Las páginas de `/<año>/` referencian `../css/…`, `../js/…`, `../fonts/…`, `../img/…` y `data-datos="../data-<huella>/"`: el build antepone `../` a todo enlace relativo del HTML fuente. Las precargas (`modulepreload`, datos del año) llevan también `../`.

**Cómo conviven producción y desarrollo en el JS** (`site/js/rutas.js`): el build pone en `<html>` `data-raiz` (`""` en la raíz, `"../"` en `/<año>/`), `data-ultimo` y, solo en `/<año>/`, `data-anio`. `urlPagina(pagina, anio)` es la única función que construye enlaces internos (menú, «Relacionado», tarjetas, selector, pie). Sin `data-raiz` (por ejemplo `site/` servido en local sin build) usa el modo de siempre, `?anio=`. En `/<año>/` manda `data-anio`; en la raíz y en local, `?anio=` o el último año.

**Compatibilidad.** En una página de la raíz, `gastos.html?anio=2025` hace `location.replace` a `2025/gastos.html` (conservando otros parámetros y el ancla); con el último año o un año inexistente no se mueve. `comparar.html?a=&b=` no cambia. El selector de año navega a la misma página del otro año (en las páginas sin año, a la portada de ese año). La `404.html` enlaza a las URLs canónicas con rutas desde la raíz.

## Despliegue con huellas

**Por qué.** El dominio está detrás de Cloudflare, que guarda css, js y vendor hasta 4 h (`cache-control: max-age=14400`). Sin huellas, tras publicar los visitantes verían ficheros viejos hasta 4 horas, y podían mezclar HTML nuevo con JS viejo. En vez de purgar la caché, cada fichero estático lleva en el nombre el hash de su contenido: si cambia el contenido, cambia la URL.

**Qué lleva huella** (`tools/build_site.py` copia `site/` a `dist/`):
- `css/styles.<hash>.css`, `css/escalas.<hash>.css`, todos los módulos `js/<nombre>.<hash>.js` y `vendor/chart.umd.min.<hash>.js` (10 hex del sha256).
- Los módulos se procesan en orden topológico y sus `import` se reescriben antes de calcular la huella: cambiar `format.js` cambia la huella de todos los que lo importan y, por tanto, la de los HTML. Un ciclo de importaciones hace fallar el build con un mensaje claro.
- Los datos: `data/` se copia a `data-<hash>/` (hash de todo el directorio) y cada HTML lleva `<html data-datos="data-<hash>/">`. `site/js/data.js` (`urlDatos`) es el único sitio que conoce la ruta; si no hay atributo (local sin build) usa `data/`. Todo el JS debe usar ese helper.
- **Sin huella:** los HTML (de entrada y enlaces entre páginas conservan su nombre). Hoy GitHub Pages los sirve con `max-age=600` y Cloudflare no los cachea (`DYNAMIC`), así que se actualizan en como mucho 10 minutos. Los `.md` de `vendor/` y `build-manifest.json` tampoco.
- `dist/build-manifest.json` relaciona cada original con su nombre publicado; `dist/` no se versiona.

**Probar `dist/` en local:**

```bash
python3 tools/build_site.py          # genera dist/ (necesita node)
python3 -m http.server -d dist 8000  # abrir http://localhost:8000
```

`site/` sigue funcionando sin build (`python3 -m http.server -d site`). Al hacer cambios: no escribas nunca rutas `data/…` a mano en el JS, usa `urlDatos`; no enlaces ficheros estáticos desde fuera de los HTML y módulos (el build solo reescribe `href`/`src` de los HTML y `from "./x.js"`); no uses `import()` dinámico ni `url()` en el CSS sin ampliar el build. Una página abierta justo antes de un despliegue puede pedir ficheros viejos que ya no existen hasta que se recargue (≤ 10 min).

## SEO y contenido rastreable

**Problema.** Todas las páginas pintan su contenido con JavaScript (`layout.js` sustituye el `<body>`), así que el HTML publicado solo decía «Cargando…». Bing, DuckDuckGo, las vistas previas y los asistentes de IA no ven nada.

**Solución (prerender en el build).** `tools/build_site.py` sustituye el `<p class="cargando">` de cada HTML de `dist/` por el marco completo (cabecera, menú, pie) y el contenido de la página con las cifras clave del año de cada página en tablas simples, `<h1>` único, enlaces «Relacionado» y un `<noscript>`. El JS sigue sustituyendo el `<body>` al cargar; el marco estático tiene las mismas clases, así que no hay salto. Los HTML de `site/` siguen mostrando «Cargando…» y funcionan en local sin build.

**Sin duplicar lógica.**
- `tools/exportar_js.mjs` (node) importa los módulos del propio JS y saca el marco (`marcoHtml`), el pie, el menú, los «Relacionado», las tarjetas de la portada, los avisos sobre préstamos (`deuda-texto.js`) y los indicadores (`lecturas.js`). **El build necesita node** (ya lo trae `ubuntu-latest`; el CI lo declara).
- `tools/prerender.py` escribe solo el contenido de cada página con las cifras de `site/data/<último>/*.json` (todo número sale de los JSON y declara el año).
- La Guía lee `site/data/guia-terminos.json`, el mismo fichero que usa el build. El texto de Metodología vive en un `<template id="contenido-estatico">` de `metodologia.html`: lo usa el build para el HTML estático y el JS en el navegador.
- Un test comprueba que las anclas de la guía y los textos de los avisos coinciden con los del JS.

**Títulos y descripciones** (únicos, título ≤ 60, descripción 120–160, sin cifras que caduquen salvo «100 €») están en el HTML fuente; `layout.js` solo añade el año: «título (2026)». El canonical nunca lleva `?anio=`; en `/<año>/` el título ya lleva el año y `layout.js` no añade nada (solo en local, sin build). `/index.html` y `/` devuelven ambos 200 (GitHub Pages no redirige): se resuelve con el canonical y porque todos los enlaces internos usan `./`.

**Rastreo.** `sitemap.xml` se genera en el build con `<lastmod>` (fecha del último commit que toca `site/`); `robots.txt` apunta a él; `404.html` (noindex, sin canonical, rutas desde la raíz, menú y lista de páginas) también. «Datos actualizados el …» del pie es la fecha del último commit que toca `site/data`. Por eso los workflows hacen `checkout` con `fetch-depth: 0`; sin historial, el build usa `SOURCE_DATE_EPOCH` o el día de hoy.

**Metodología y fuentes** (`metodologia.html`): origen de los datos, presupuesto aprobado frente a ejecutado, clasificación (órdenes EHA/3565/2008 y HAP/419/2014), población del INE, estimaciones, actualización, errores y aviso de textos de préstamos y remanentes pendientes de revisión (`docs/revision/`).

### Datos estructurados y rendimiento

- **JSON-LD** (`tools/seo.py`, bloque `application/ld+json` en el `<head>`, generado en el build; es un bloque de datos y no incumple la CSP): portada con `WebSite` y `GovernmentOrganization` enlazados por `@id` (logo = escudo con huella, `sameAs` = <https://github.com/arandadeduero>); `BreadcrumbList` en las páginas interiores; un `Dataset` por año en Descargas (JSON con huella y Excel originales como `DataDownload`); `WebApplication` gratuita en la calculadora; `DefinedTermSet` en la guía desde `guia-terminos.json`. No se usan `FAQPage` ni `SearchAction`. Cada `Dataset` lleva `license` (**CC BY 4.0**, https://creativecommons.org/licenses/by/4.0/) y `creditText` («Ayuntamiento de Aranda de Duero»); ver `LICENSE-DATOS.md`.
- **Precarga** (build): `modulepreload` del módulo de cada página y de sus imports, y `preload` (`as="fetch" crossorigin`) de `index.json` y de los JSON que lee esa página (se deducen de su código, `load("…")`) del último año. Así la petición de datos empieza al leer el `<head>` y no tras bajar la cadena de módulos. Si alguien abre un año que no es el último, el navegador avisa en consola de que la precarga no se usó (solo aviso, y solo con `?anio=` distinto del último).
- `getIndex` y `loadData` cachean por ruta (una sola petición a `index.json`); la portada pide `gastos.json` (el más pesado) después de pintar, solo para la tarjeta «¿Cuánto gasta…?»; Chart.js solo va en las páginas con gráficos y con `defer` (se ejecuta antes del módulo, en orden).
- **Saltos de diseño (CLS):** si el HTML ya trae el marco estático, `layout.js` solo rellena cabecera y pie en su sitio y deja el contenido estático hasta que la página pinta el suyo (antes, quitar y volver a crear el pie daba un CLS de 0,28); `comparar` y `calculadora` reservan altura con la clase `.alto`; la tarjeta de la portada con `.destacado-caja`.

## Tipografía

La web usa **Outfit** (SIL Open Font License 1.1), descargada de Fontsource y alojada en `site/fonts/` (sin Google Fonts ni CDN). Se declara con `@font-face` en `css/styles.css`, se precarga en cada página y el build le pone huella como al resto de ficheros. Detalles y cómo actualizarla: `site/fonts/README.md`.

## Actualizar Chart.js

```bash
npm pack chart.js     # descargar la última versión
# copiar dist/chart.umd.min.js y LICENSE.md a site/vendor/ y anotar la versión en site/vendor/README.md
```

## Notas sobre los datos

- Los totales salen de la hoja «<año>» de `A1`. En `A9` (inversiones) y `A12` se usa la hoja «<año>», no las «Copia de…» ni las hojas de trabajo.
- El préstamo previsto de 11 M€ (anexo de deuda de 2025 y 2026) no entra en la deuda del titular ni en el gráfico: es una previsión que solo se formalizará si es necesario. La web muestra también los 20,16 M€ de préstamo de la financiación de inversiones, sin afirmar la causa de la diferencia.
- **Nivel de endeudamiento** (página Indicadores): deuda viva a 31 de diciembre del año del presupuesto (solo los préstamos del anexo de deuda; aparte, con el préstamo previsto) dividida entre los ingresos corrientes (capítulos 1 a 5 de ingresos) del presupuesto. Es una **estimación**: el art. 53 del TRLRHL (RDL 2/2004) y la disposición final 31.ª de la Ley 17/2012 (que da nueva redacción a la disposición adicional 14.ª del RDL 20/2011) lo calculan con el capital vivo a 31/12 del año anterior (todas las operaciones a corto y largo plazo y avales, más la operación proyectada) sobre los ingresos corrientes **liquidados** del año anterior, descontando los ingresos afectados y extraordinarios. Umbrales legales: hasta el 75 % (con ahorro neto positivo) sin autorización para financiar inversiones; entre el 75 % y el 110 %, con autorización de la tutela financiera; por encima del 110 % (o con ahorro neto negativo), no se pueden concertar préstamos a largo plazo. El 60 % del PIB de la LOEPSF (art. 13, 3 % del PIB para el conjunto de corporaciones locales) es un límite del conjunto de las administraciones sobre el PIB nacional, no un porcentaje de los ingresos de un ayuntamiento. No hay ningún límite del 40 % en esa normativa.
- Los importes «por habitante» dividen el gasto entre la población del INE (INE: 33.757 habitantes en 2024, 33.956 en 2025; 2026 usa el dato de 2025, el último disponible); no son lo que paga cada vecino.
- Ideas tomadas de otros visores (Gobierto Presupuestos, visor de Fuengirola): ver el apartado correspondiente del diseño. Para comparar con otros municipios: [Gobierto Presupuestos](https://presupuestos.gobierto.es/municipios/aranda-de-duero).

## Licencia

- **Código**: [MIT](LICENSE) © 2026 Ayuntamiento de Aranda de Duero. Chart.js tiene su propia licencia (MIT), en `site/vendor/`; Outfit, la suya (SIL OFL 1.1), en `site/fonts/`.
- **Datos** (los Excel de `2024/`, `2025/` y `2026/` y los JSON de `site/data/`): [Creative Commons Reconocimiento 4.0 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/), ver [LICENSE-DATOS.md](LICENSE-DATOS.md). Para citar: «Fuente: Ayuntamiento de Aranda de Duero (presupuestos.arandadeduero.dev), licencia CC BY 4.0». Los `Dataset` del JSON-LD (`tools/seo.py`) y la página de descargas la declaran.
