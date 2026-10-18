# Visor de presupuestos municipales de Aranda de Duero — diseño

Fecha: 2026-10-19

## Intención y porqué

Una web estática para que **cualquier vecino de Aranda de Duero, sin conocimientos de presupuestos**, entienda el presupuesto del Ayuntamiento. La pregunta que debe responder la portada es: **«¿en qué se gasta mi dinero?»**.

Referencias de otros ayuntamientos (solo como inspiración de estructura, no para copiar): https://presupuestos.eibar.eus/eusk/budgets y https://pressupostos.xativa.es/resumen/#2026.

## Objetivos

- Portada que contesta la pregunta antes de pedir al vecino que explore.
- Selector de año. Hoy solo existe **2026, presupuesto inicial** (previsiones, no gastos ejecutados). Añadir otro año debe ser: poner sus Excel en una carpeta `AAAA/`, ejecutar la conversión y publicar.
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

## Deja al constructor

- Librería de gráficos (preferiblemente ligera, o SVG propio), estilo visual, estructura de carpetas y de JSON, naming de ficheros, sistema de rutas (páginas separadas o una sola con hash).
- Cómo se resuelven las discrepancias de los Excel, documentándolas.
- Accesibilidad y responsive (móvil primero, dado el público).
- Texto exacto de las traducciones de capítulos y programas.
