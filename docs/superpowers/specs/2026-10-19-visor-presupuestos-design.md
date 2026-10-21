# Visor de presupuestos municipales de Aranda de Duero — diseño

Fecha: 2026-10-19

## Intención y porqué

Una web estática para que **cualquier vecino de Aranda de Duero, sin conocimientos de presupuestos**, entienda el presupuesto del Ayuntamiento. La pregunta que debe responder la portada es: **«¿en qué se gasta mi dinero?»**.

Referencias de otros ayuntamientos (solo como inspiración de estructura, no para copiar): https://presupuestos.eibar.eus/eusk/budgets y https://pressupostos.xativa.es/resumen/#2026.

## Objetivos

- Portada que contesta la pregunta antes de pedir al vecino que explore.
- Selector de año. Hoy solo existe **2026, presupuesto aprobado** (previsiones, no gastos ejecutados). Añadir otro año debe ser: poner sus Excel en una carpeta `AAAA/`, ejecutar la conversión y publicar.
- Secciones: **Resumen, Ingresos, Gastos, Inversiones, Subvenciones, Deuda y carga financiera**.
- Lenguaje llano: los nombres técnicos se traducen («Gastos corrientes en bienes y servicios» → «Servicios y mantenimiento»); el nombre oficial es visible al pasar el ratón o en un detalle.
- Publicable en **GitHub Pages**, sin servidor.

## No objetivos

- Ejecución presupuestaria (gastos realmente realizados). Hoy no hay datos; el diseño no debe impedir añadirlos más tarde.
- Edición de datos, cuentas de usuario, backend, analítica.
- Cubrir las Bases de Ejecución (`A4 …docx`): no se usan.

## Anti-objetivo

**Que un vecino sin conocimientos se líe.** Una página técnicamente correcta pero que exige saber qué es un capítulo, un programa o el remanente de tesorería es un fallo. Ante la duda, menos información visible por defecto y el detalle bajo demanda.

## Restricciones

- **HTML y JavaScript simples**, sin framework. Datos servidos como ficheros estáticos (JSON).
- Fuente de datos: los Excel de `2026/` (A1 resumen, A2 ingresos, A3 gastos, A9 inversiones, A12 subvenciones, A13.1 deuda, A13.2 carga financiera).
- Los Excel tienen rarezas: celdas con `#REF!`, columnas de trabajo y una hoja «Líneas Fundamentales» en A1 con cifras distintas. **Fuente de verdad: la hoja «2026»** de A1 (total 64.280.861,35 €), salvo indicación contraria.
- Los Excel se convierten a JSON con un script reproducible (los datos del navegador no leen Excel). El JSON generado se commitea.
- Despliegue en GitHub Pages, incluida la configuración (workflow de GitHub Actions o carpeta publicada) y las instrucciones para activarlo.

## Decisiones del usuario

### Portada
- Opción elegida: **«responde primero, explora después»**.
- Barra superior con nombre del sitio y selector de año.
- Titular «Por cada 100 € que gasta el Ayuntamiento en 2026…» con una barra dividida en grandes bloques (obras e inversiones, servicios, personal, otros), cada uno con su importe por cada 100 €.
- Total del presupuesto y comparación con 2025.
- Accesos al detalle: ingresos, inversiones, subvenciones, deuda.

### Gastos
- Navegación de general a concreto: capítulo → programa → partida.
- **Capítulo 1 (personal): solo el total por programa**; sin sueldos por grupo, trienios, etc.
- **Capítulos 2 a 9: hasta la partida.**

### Deuda
- Tabla de préstamos: fecha de concesión, entidad, importe, tipo de interés, año final, lo que queda por pagar.
- Gráfico de deuda viva por año con la previsión de los años siguientes, **solo con los préstamos existentes**.
- Deuda total prevista a 31/12/2026 como titular.
- El **préstamo previsto de 11 M€ (marzo 2026, entidad sin indicar, amortización 2027-2037)** se destaca en un **recuadro como previsión**, **no entra en el gráfico** porque no es firme.
- Carga financiera (capital + intereses al año) a partir de A13.2.

### Inversiones
- Qué se invierte, agrupado por programa, con importe por proyecto.
- Para cada obra, **cómo se financia**: préstamo, ingresos corrientes, otros, remanente de tesorería (RTA).
- Aviso explícito: el Ayuntamiento usa **remanentes** para pagar parte de las inversiones, por lo que el préstamo final puede ser menor de 11 M€. El remanente depende de lo comprometido y de lo realmente no ejecutado, así que se presenta como **estimación**. El aviso se enlaza también desde el recuadro de la página de deuda.

### Subvenciones
- Buscador por entidad que muestra cuánto recibe cada una.
- Agrupación por programa (tipo de actividad subvencionada) con totales.

## Decisiones tomadas por mí (a revisar)

- Gastos: vista principal con gráfico de bloques/barras desplegable y tabla con buscador por palabra debajo; comparación con 2025 en cada cifra.
- «Gastos» y «Resumen» se funden en la portada y en una página de detalle de gastos.
- Ingresos: misma estructura que gastos (capítulo → partida) con comparación 2024/2025/2026 (los Excel ya lo traen). Resumen: ingresos frente a gastos.
- Subvenciones: cada fila muestra además objeto del convenio y diferencia con 2025.
- Inversiones: la financiación por proyecto se muestra como barra pequeña más un resumen general por fuente.
- Los textos de explicación («¿qué es esto?») acompañan cada sección en lenguaje llano.
- Idioma: castellano.

## Respuestas del usuario tras la revisión

- **Recuadro de previsión (deuda):** muestra **las dos cifras, explicadas**: 11 M€ (anexo de deuda, préstamo previsto en marzo de 2026) y 20,16 M€ (préstamo que financia inversiones en A9 y en el capítulo 9 de ingresos). El texto debe explicar la diferencia entre ambas; el usuario atribuye la diferencia al uso de remanentes, pero los ficheros no lo confirman: el constructor la presenta de forma que no afirme más de lo que dicen los datos y deja el texto final a revisión del usuario.
- **Titular de la deuda a 31/12/2026:** **solo con los préstamos existentes** (2.181.340,81 €). Junto a él se menciona la previsión de 11 M€, indicando que **solo se formalizará si es necesario**, según la liquidación y la ejecución presupuestaria.

## Aclaraciones tras la revisión del documento

Resueltas con los datos del proyecto:
- **Inversiones (A9):** usar la hoja «2026», no «Copia de 2026». Su total del capítulo VI (24.206.942,85 €) coincide con A1 y A3; la copia suma 25,3 M€ y es un borrador. Las filas con notas de trabajo («!!!», «Pluri??») no se muestran como tales.
- **Cuadre:** el total de gastos de A3 (64.280.861,35 €) coincide con A1. El script de conversión **avisa** si algún total no cuadra con A1, sin romper la generación.
- **Fuentes de financiación de inversiones:** A9 tiene cinco: préstamo, ingresos corrientes, otros, remanente (RTA, cap. 8) y **subvenciones**. Se muestran las cinco. En proyectos de varios años se muestra solo la parte de 2026.
- **Deuda (A13.1):** el fichero trae deuda viva desde 01/01/2023. Con solo los tres préstamos existentes, la deuda a 01/01/2026 es 2.713.393,77 € y a 31/12/2026 es 2.181.340,81 €; con el préstamo previsto de 11 M€ sería 13.181.340,81 €. Los años siguientes se calculan con las amortizaciones constantes de cada préstamo. Los intereses son variables (Euribor + diferencial): el diferencial se muestra como texto y la carga financiera sale de A13.2.
- **Repositorio:** `github.com/arandadeduero/visorpresupuesto`. Se sirve como página de proyecto (subruta `/visorpresupuesto/`), así que todas las rutas son relativas.

Decisiones mías:
- «Por cada 100 €» se calcula sobre el **total de gastos** (64,28 M€). Bloques: **Obras e inversiones** = cap. 6 y 7; **Servicios** = cap. 2; **Personal** = cap. 1; **Otros** = cap. 3, 4, 5, 8 y 9 (intereses, transferencias, deuda y fondo de contingencia).
- Comparación con 2025: columna «créditos 2025» de A1, A3 y A2; si una sección no trae datos de 2025, no se muestra comparación. Se etiqueta como «presupuesto 2025».
- Traducciones a lenguaje llano: solo capítulos y programas, escritas a mano. Las partidas se muestran con el nombre del Excel, con mayúsculas normalizadas.
- Flujos de ARU y filas de trabajo de A1 (`#REF!`, cuenta remunerada, UNESPA): no se muestran, salvo que formen parte de los totales oficiales.

## Identidad visual y dependencias (indicado por el usuario al aprobar)

Colores del Ayuntamiento (HTML): rojo `#ce0e2d` (Pantone 186C), ámbar `#f5a800` (130C), marrón `#a4541c` (160C), azul `#0083c1` (7460C), azul claro `#e9f4f9` (7460C 8 %), gris `#646464` (negro 75 %), gris oscuro `#3c3c3c` (negro 90 %), celeste `#3cb4e5` (298C).

Las librerías de gráficos **se descargan y se guardan en `site/vendor/`** (no CDN), siempre en su **última versión** disponible al construir.

Decisiones mías añadidas al preparar el plan:
- En la página de gastos, el vecino puede agrupar **por programa** («¿en qué?», con las áreas de gasto: servicios básicos, protección social, sanidad/educación/cultura/deporte, economía, administración general, deuda) o **por tipo de gasto (capítulo)**. Por defecto, por programa. Ambos llegan hasta la partida (salvo personal).
- Existe una página breve de **Resumen** (ingresos frente a gastos por capítulo).
- El conversor de Excel está en Python con `openpyxl`; el JSON generado se commitea y GitHub Pages solo publica la carpeta `site/`.

## Ideas tomadas de otros visores (Gobierto y Fuengirola)

Analizados el 2026-10-19: *Gobierto Presupuestos* (presupuestos.gobierto.es, Aranda de Duero 2024) y el visor de Fuengirola (gobiernoabierto.fuengirola.es/pre, de oGov).

Integrado, siempre calculado con nuestros datos:
- **Euros por habitante** en portada, gastos e ingresos, con la población del INE (33.956 habitantes en 2025) indicada como fuente y con el aviso de que no es lo que paga cada vecino.
- **Políticas de gasto** con nombre llano (Cultura, Deporte, Bienestar comunitario…), a partir de los dos primeros dígitos del programa y la clasificación oficial por programas; sustituyen a las áreas en la vista «¿En qué se gasta?».
- **«¿Cuánto gasta Aranda de Duero en…?»** con «Enséñame otra» en la portada y **«Qué ha cambiado más»** (suben y bajan) en el resumen.
- **Indicadores** (impuestos y tasas por habitante, ahorro bruto y neto estimado, deuda por habitante, nivel de endeudamiento estimado frente a los umbrales legales del 75 % y el 110 % (art. 53 TRLRHL y DF 31.ª de la Ley 17/2012; estimación con el presupuesto aprobado, la ley usa la liquidación del año anterior), coste anual de la deuda, dependencia de transferencias), **calculadora** («¿a qué se destina lo que pago?», reparto proporcional y orientativo con los importes que escribe el vecino), **guía** con glosario, **descargas** de los JSON y explicación breve de cada forma de ver los gastos.
- Enlace a Gobierto para comparar con otros municipios.

Descartado: series históricas 2010–2024, medias provincial, autonómica y nacional, rankings, ejecución presupuestaria (los Excel solo traen el presupuesto aprobado y datos de terceros no son comparables), calculadora con ordenanzas fiscales (no disponemos de ellas) y clasificación orgánica («¿quién gasta?»), que los Excel no traen.

## Deja al constructor

- Librería de gráficos (preferiblemente ligera, o SVG propio), estilo visual, estructura de carpetas y de JSON, naming de ficheros, sistema de rutas (páginas separadas o una sola con hash).
- Cómo se resuelven las discrepancias de los Excel, documentándolas.
- Accesibilidad y responsive (móvil primero, dado el público).
- Texto exacto de las traducciones de capítulos y programas.


## Varios ejercicios (2024, 2025 y 2026)

**Diseño.** Cada año vive en `site/data/<año>/` con los mismos seis JSON; `site/data/index.json` los lista y el último es el año por defecto. Los JSON usan claves genéricas (`anterior`, `actual`, `anterior2`) en lugar de `y2025`/`y2026`: ninguna página ni test conoce un año concreto (un test lo vigila), y añadir un ejercicio es copiar la carpeta de Excel, añadir su población y ejecutar `tools/convert.py`. Lo que no existe en un año se representa con `null` y la web omite el texto asociado.

**Diferencias halladas entre los Excel.**
- Nombres: `A13.1`/`A13.2` se llaman «Estado de la deuda» / «Carga Financiera» (2024) o «… CON PRESTAMO FUTURO» (2025, 2026); el conversor busca por prefijo `A13.1`.
- Posición de columnas: A3 2024 lleva una columna más antes de los importes; A9 2024 empieza en la columna A (no en B); A13.1 2024 y 2025 tienen una columna vacía más que 2026. Se localizan por rótulo.
- A2: 2024 titula «PREVISIONES» a la columna del año anterior y solo trae dos años; 2025 también dos; 2026 trae tres. Total roto con `#REF!` en el capítulo VIII y en el total general de 2024: se recompone sumando conceptos. Las previsiones iniciales de 2023 de A2 no coinciden con los «créditos 2023» de A1 en el capítulo VII (741.064,55 € frente a 5.033.675,76 €): cada fichero mantiene su base.
- A3: «CAPITULO» sin tilde en 2024. La columna del año anterior no trae las inversiones (capítulo VI) en 2024 ni en 2025: esas partidas quedan con `anterior = null` y los capítulos usan los créditos del año anterior de A1.
- A9 2025: el programa 9240 aparece dos veces (un bloque antiguo de 5.000 € y el bueno de 345.000 €, que coincide con A3 y con el total); vale el último. Algunos programas difieren entre A3 y A9 en 2025 (1600/1610/1623/3200/3220) aunque el total coincide. A9 2024 contiene hojas de trabajo ajenas a la tabla (propuestas por grupo político, listados).
- A12: el crédito de la partida es el texto «Loading...» en 2025 (`credito = null`); los nombres vienen en mayúsculas en 2024; algunas filas de partida llevan también la primera entidad (Sonorama, ASOHAR, Consorcio Ruta del Vino…) y debajo de un título (Turismo, Desarrollo económico); hay dos bloques (nominativas y cuotas). En 2024 la celda «TOTAL SUBVENCIONES NOMINATIVAS» (752.250 €) es 95.000 € menor que la suma de los subtotales de sus programas.
- Deuda: en 2024 no hay préstamo previsto; en 2025 el previsto se firmaría en marzo de 2025 (en 2026, marzo de 2026). La etiqueta «TOTAL INTERESES 2024» del A13.2 de 2025 es en realidad la de 2025.
- Totales: 2024 y 2026 cuadran (ingresos = gastos). En 2025 el Excel trae 250.000 € más de ingresos que de gastos (65.078.315,20 € frente a 64.828.315,20 €); el presupuesto de 2026 ya recoge un capítulo 2 de 2025 con 250.000 € más. El conversor lo trata como nota conocida y la web la enseña en el resumen.
- Para comparar presupuestos entre sí, usar el `actual` de cada año: el `anterior` de un año no siempre coincide con el `actual` del anterior (ver el caso de 2025).
- Población INE: 2024 → 33.757; 2025 → 33.956; 2026 → 33.956 (dato de 2025, el último disponible).

## Comparar dos presupuestos (`comparar.html`)

**Qué es.** Página «Comparar» para elegir dos presupuestos de `site/data/index.json` y ver qué ha cambiado. Los años van en la URL (`?a=2024&b=2026`, en cualquier orden, compartible; por defecto el penúltimo frente al último; nunca el mismo año dos veces). También se guardan `vista`, `modo`, `orden` y `clave`. La cabecera oculta el selector de año único.

**Contenido.** Titular con gastos e ingresos de cada año y la diferencia; vistas «Gastos por política» (por defecto), «Gastos por capítulo», «Ingresos por capítulo» e «Indicadores» (lado a lado, con `calcularIndicadores`); interruptor «Total / Por habitante» (población de cada año en `resumen.json`); barras pareadas HTML/CSS (azul `#0083c1` el primer año, ámbar `#f5a800` el segundo; los importes van fuera de la barra), diferencia en euros y %, etiquetas «nuevo» / «desaparece», las tres frases más destacadas generadas, orden por importe, subida, bajada, % o nombre, tabla equivalente y evolución de la categoría elegida en todos los años (Chart.js con leyenda y tabla). Aviso visible: son presupuestos aprobados (previsiones) y euros corrientes, sin inflación.

**Reglas.** Se compara siempre el `actual` de cada año con el `actual` del otro (nunca `anterior` con `actual`). Lógica pura y probada en `site/js/comparacion.js`; la pintan `site/js/comparar.js`. Una categoría con importe 0 o ausente en un año y positivo en el otro es «nuevo» (o «desaparece»); el % es `null` si el punto de partida es 0, así que no hay NaN ni Infinity.

**Equivalencias entre 2024, 2025 y 2026 (comprobadas).** Los códigos y nombres de las 21 políticas y de los nueve capítulos de gastos e ingresos coinciden; la única diferencia es la política 46 «Investigación, desarrollo e innovación», que solo existe en 2026 (sale «nuevo»). No hace falta mapeo. No se comparan programas ni partidas (sus códigos sí han variado en detalle); queda como mejora futura.


## Capítulos y artículos

**Petición.** «Agrupar a nivel de capítulo, sobre todo en los quesitos, y poder ver a nivel de Préstamos / Impuestos indirectos…». Interpretación: los **capítulos** (9 bloques) son la vista principal y por defecto de todos los quesitos; lo que el usuario describe como «Préstamos / Impuestos indirectos» es el **artículo**, el nivel siguiente de la clasificación económica (dos primeros dígitos del código; Gobierto lo usa en su top de ingresos).

**Datos.** El artículo se deriva del código: ingresos, `concepto[:2]`; gastos, `partida[:2]` (también en el capítulo 1, aunque la web no baje de ahí). Se agrupa **por código**, no por las filas «ARTÍCULO nn» del Excel de ingresos, que en 2024 y 2025 cuenta la tasa 329.03 (800 €) dentro del artículo 33 en lugar del 32; el total del capítulo no cambia. Los nombres oficiales se tomaron de los anexos de la Orden EHA/3565/2008 (BOE n.º 297, 10-12-2008) y se contrastaron con la Orden HAP/419/2014, que crea el artículo 50 (Fondo de Contingencia) y **suprime el artículo 27**. En 2026 el Excel todavía usa el código 277 (un contrato de la escuela de cerámica): se le da el nombre neutro «Otros gastos en bienes y servicios» y se anota en `labels.py`. Cada artículo lleva `nombre` (corto y llano) y `oficial`.

**Web.**
- Selector accesible «Ver por: Capítulos | Artículos» (grupo de botones con `aria-pressed`, capítulos por defecto) en cada quesito.
- Vista por artículos: cada artículo lleva el color de su capítulo en distintos tonos (el del capítulo, más claro, más oscuro…); las porciones de un capítulo van juntas; en cada capítulo los artículos por debajo del 2 % del total se agrupan en «Otros artículos de <capítulo>» (solo si hay al menos dos y queda alguno grande); como no se pueden distinguir ~20 categorías por color, la leyenda va agrupada por capítulo con nombre, porcentaje e importe de cada artículo y el nombre oficial al pasar el ratón.
- Listas: Ingresos pasa a capítulo → artículo → concepto; en Gastos, «¿Qué tipo de gasto es?» pasa a capítulo → artículo → partida (el programa es el detalle de la partida; el personal acaba en el artículo). «¿En qué se gasta?» (políticas) no cambia ni deja de ser la vista inicial de Gastos.
- La Guía recoge «Artículo» y «Concepto».

## Despliegue con huellas

Cloudflare cachea css/js 4 h, así que el despliegue publica `dist/`, generado por `tools/build_site.py`: css, js (módulos con los `import` reescritos, huella en orden topológico), vendor y la carpeta de datos (`data-<huella>/`, indicada en `<html data-datos>` y leída solo desde `data.js`) llevan el hash del contenido en el nombre. Los HTML conservan nombre (caché corta, 10 min). `site/` sigue funcionando sin build. Detalles y uso local en el README.

## Tema claro/oscuro, variables y sin estilos en línea

Petición: «una versión en oscuro; sin estilos inline, solo CSS; todos los colores son variables; que claro/oscuro haga match del sistema». Decisiones:

- **Solo el sistema decide** (`prefers-color-scheme`, `color-scheme: light dark`); sin interruptor manual. Reacciona en vivo, incluidos los gráficos.
- **Tokens en dos capas:** paleta municipal como constantes y tokens semánticos que las referencian. El oscuro redefine solo los semánticos (y los de capítulo/serie/tono), con sus propias constantes (`--n-*`, `--rojo-d`…). Un test impide literales de color fuera de los bloques `:root` y otro fija el contraste (4,5:1 texto; 3:1 texto grande, foco y gráficos) de los pares reales en ambos temas.
- **Valores dinámicos sin inline:** escalas de clases generadas (`.ancho-N` 0–100 %, `.crece-N` 1–100, redondeadas; todo lo que es > 0 se ve) y clases de color (`.serie-N`, `.cap-N-tono-K`) que fijan `--color`/`--sobre`. Los seis tonos de los artículos son `--cap-N-tono-K = color-mix(--cap-N, --tono-K)`; en oscuro los tonos solo se aclaran.
- **Chart.js:** los colores se leen de las variables (`colorVar`, normalizadas a `rgb()` mediante un canvas) y se pasan como opciones scriptable; al cambiar el esquema se llama a `update()` en todas las instancias.
- **CSP por `<meta>`** (`style-src 'self'`, `script-src 'self'`): activada, porque Chart.js solo usa CSSOM. El script de aviso de `file://` pasa a fichero propio. `frame-ancestors` no se puede fijar por `<meta>`, así que no se incluye.
- El tono del texto sobre los bloques de color de la portada en claro se mantiene (3:1, texto grande en negrita), como antes.

## Analítica y privacidad

Decisión (petición del usuario, siguiendo la implementación del repositorio `contratacion-estado`): Google Analytics 4 con consentimiento previo (RGPD).

- Nada se carga ni se envía a Google hasta «Aceptar». «Aceptar» no caduca; «Rechazar» caduca a los 4 días. Do Not Track lo oculta todo. El enlace «Preferencias de analítica» del pie retira el consentimiento, borra las cookies `_ga*` y vuelve a preguntar.
- Lógica pura y testeable en `site/js/analytics.js`; valores (ID, clave de `localStorage`, TTL, política de privacidad del Ayuntamiento) en `site/js/analytics-config.js`; se monta desde `layout.js`, así que no se toca el HTML de las páginas.
- El aviso es una tarjeta fija abajo (`role="region"`), con clases CSS y tokens existentes (sin colores ni estilos en línea), botones de al menos 44 px, foco visible y sin animación con `prefers-reduced-motion`.
- La CSP de las 12 páginas añade solo los dominios de GA4/GTM necesarios (`script-src`, `img-src`, `connect-src`); el código solo los usa con consentimiento. Sin `unsafe-inline` ni `unsafe-eval`.
- No se redacta texto legal propio: se enlaza la política del Ayuntamiento, que conviene revisar con él.

## SEO: contenido estático rastreable

**Problema.** Todas las páginas pintan su contenido con JavaScript (`layout.js` sustituye el `<body>`), así que el HTML publicado solo decía «Cargando…». Bing, DuckDuckGo, las vistas previas y los asistentes de IA no ven nada.

**Solución (prerender en el build).** `tools/build_site.py` sustituye el `<p class="cargando">` de cada HTML de `dist/` por el marco completo (cabecera, menú, pie) y el contenido de la página con las cifras clave del último año en tablas simples, `<h1>` único, enlaces «Relacionado» y un `<noscript>`. El JS sigue sustituyendo el `<body>` al cargar; el marco estático tiene las mismas clases, así que no hay salto. Los HTML de `site/` siguen mostrando «Cargando…» y funcionan en local sin build.

**Sin duplicar lógica.**
- `tools/exportar_js.mjs` (node) importa los módulos del propio JS y saca el marco (`marcoHtml`), el pie, el menú, los «Relacionado», las tarjetas de la portada, los avisos sobre préstamos (`deuda-texto.js`) y los indicadores (`lecturas.js`). **El build necesita node** (ya lo trae `ubuntu-latest`; el CI lo declara).
- `tools/prerender.py` escribe solo el contenido de cada página con las cifras de `site/data/<último>/*.json` (todo número sale de los JSON y declara el año).
- La Guía lee `site/data/guia-terminos.json`, el mismo fichero que usa el build. El texto de Metodología vive en un `<template id="contenido-estatico">` de `metodologia.html`: lo usa el build para el HTML estático y el JS en el navegador.
- Un test comprueba que las anclas de la guía y los textos de los avisos coinciden con los del JS.

**Títulos y descripciones** (únicos, título ≤ 60, descripción 120–160, sin cifras que caduquen salvo «100 €») están en el HTML fuente; `layout.js` solo añade el año: «título (2026)». El canonical nunca lleva `?anio=`. `/index.html` y `/` devuelven ambos 200 (GitHub Pages no redirige): se resuelve con el canonical y porque todos los enlaces internos usan `./`.

**Rastreo.** `sitemap.xml` se genera en el build con `<lastmod>` (fecha del último commit que toca `site/`); `robots.txt` apunta a él; `404.html` (noindex, sin canonical, rutas desde la raíz, menú y lista de páginas) también. «Datos actualizados el …» del pie es la fecha del último commit que toca `site/data`. Por eso los workflows hacen `checkout` con `fetch-depth: 0`; sin historial, el build usa `SOURCE_DATE_EPOCH` o el día de hoy.

**Metodología y fuentes** (`metodologia.html`): origen de los datos, presupuesto aprobado frente a ejecutado, clasificación (órdenes EHA/3565/2008 y HAP/419/2014), población del INE, estimaciones, actualización, errores y aviso de textos de préstamos y remanentes pendientes de revisión (`docs/revision/`).

### Datos estructurados y rendimiento

- **JSON-LD** (`tools/seo.py`, bloque `application/ld+json` en el `<head>`, generado en el build; es un bloque de datos y no incumple la CSP): portada con `WebSite` y `GovernmentOrganization` enlazados por `@id` (logo = escudo con huella, `sameAs` = <https://github.com/arandadeduero>); `BreadcrumbList` en las páginas interiores; un `Dataset` por año en Descargas (JSON con huella y Excel originales como `DataDownload`); `WebApplication` gratuita en la calculadora; `DefinedTermSet` en la guía desde `guia-terminos.json`. No se usan `FAQPage` ni `SearchAction`. **Falta la licencia:** los `Dataset` no llevan `license` porque aún no se ha decidido la de los datos; cuando se decida hay que añadirla en `seo.dataset()` (y publicarla en README y Metodología).
- **Precarga** (build): `modulepreload` del módulo de cada página y de sus imports, y `preload` (`as="fetch" crossorigin`) de `index.json` y de los JSON que lee esa página (se deducen de su código, `load("…")`) del último año. Así la petición de datos empieza al leer el `<head>` y no tras bajar la cadena de módulos. Si alguien abre un año que no es el último, el navegador avisa en consola de que la precarga no se usó (solo aviso, y solo con `?anio=` distinto del último).
- `getIndex` y `loadData` cachean por ruta (una sola petición a `index.json`); la portada pide `gastos.json` (el más pesado) después de pintar, solo para la tarjeta «¿Cuánto gasta…?»; Chart.js solo va en las páginas con gráficos y con `defer` (se ejecuta antes del módulo, en orden).
- **Saltos de diseño (CLS):** si el HTML ya trae el marco estático, `layout.js` solo rellena cabecera y pie en su sitio y deja el contenido estático hasta que la página pinta el suyo (antes, quitar y volver a crear el pie daba un CLS de 0,28); `comparar` y `calculadora` reservan altura con la clase `.alto`; la tarjeta de la portada con `.destacado-caja`.

## URLs propias por año

**Problema.** El año iba en `?anio=` y el canonical no lo incluía: «presupuesto Aranda de Duero 2025» no tenía página propia.

**Diseño.** Una carpeta por año publicado con las 9 páginas que dependen de él (`/2025/`, `/2025/gastos.html`...; los años salen de `index.json`). La raíz es el último año: `/` (portada, con bloque «Presupuestos por año») y alias `/gastos.html`... con canonical a `/2026/gastos.html`; `/2026/` tiene canonical `/`. Comparar, guía, metodología y descargas no dependen del año y se quedan en la raíz. El sitemap solo lista páginas con canónica propia (31 URLs).

**Decisiones.**
- Los alias se conservan (no hay redirecciones en GitHub Pages) y se resuelven con canonical, no con `noindex`, para pasar la señal de enlaces al canónico.
- Rutas relativas con profundidad (`../`) reescritas por el build sobre el mismo HTML fuente; el JS no calcula rutas a mano: `rutas.js` (`urlPagina`) lee `data-raiz`, `data-ultimo` y `data-anio` de `<html>`. Sin `data-raiz` (`site/` sin build) se mantiene `?anio=`: un solo `if` en `urlPagina`, `destinoAntiguo` y `urlCambioDeAnio`, con tests en ambos modos.
- El HTML estático se calcula por «entorno» (cada año y la raíz) ejecutando el propio JS (`tools/exportar_js.mjs` simula esos `data-*`): enlaces, avisos, indicadores y «Otros años» no tienen segunda copia en Python.
- Las páginas sin año no arrastran el año en la URL en producción (enlaces limpios); en local sí (`?anio=`).
- Miga «Presupuesto 2025» → `/2025/` también para el último año (su carpeta existe y es la misma página).

