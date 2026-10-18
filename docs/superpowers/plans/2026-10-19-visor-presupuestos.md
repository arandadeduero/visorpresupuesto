# Visor de presupuestos de Aranda de Duero — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Web estática (GitHub Pages) que explica a cualquier vecino el presupuesto inicial 2026 del Ayuntamiento, partiendo de los Excel de `2026/`.

**Architecture:** Un conversor Python (`tools/`) lee los Excel y genera JSON en `site/data/<año>/`. Las páginas HTML/JS simples de `site/` leen ese JSON con `fetch` y dibujan gráficos con Chart.js vendorizado. GitHub Actions publica solo `site/`.

**Tech Stack:** Python 3 + openpyxl + pytest (conversor); HTML, CSS y JavaScript ES modules sin framework; Chart.js (última versión, en `site/vendor/`); `node --test` para funciones puras de JS; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-19-visor-presupuestos-design.md`

## Global Constraints

- HTML y JS simples, sin framework. Rutas **relativas** (el sitio vive en `/visorpresupuesto/`).
- Librerías en `site/vendor/`, **última versión** al construir, sin CDN. Anotar versión y licencia en `site/vendor/README.md`.
- Colores: rojo `#ce0e2d`, ámbar `#f5a800`, marrón `#a4541c`, azul `#0083c1`, azul claro `#e9f4f9`, gris `#646464`, gris oscuro `#3c3c3c`, celeste `#3cb4e5`. Texto blanco solo sobre rojo, azul, gris y gris oscuro; sobre ámbar y celeste, texto `#3c3c3c`.
- Castellano. Lenguaje llano: capítulos y programas traducidos a mano; partidas con el nombre del Excel (mayúsculas normalizadas); el nombre oficial visible al pasar el ratón / en el detalle.
- Fuente de verdad de totales: hoja «2026» de A1 (gastos = ingresos = 64.280.861,35 €). En A9 usar la hoja «2026», **nunca** «Copia de 2026».
- Capítulo 1 (personal): solo total por programa. Capítulos 2–9: hasta la partida.
- El conversor avisa (no falla) si un total no cuadra con A1.
- Deuda: gráfico y titular a 31/12/2026 **solo con préstamos existentes** (2.181.340,81 €). El préstamo previsto de 11 M€ (anexo de deuda) y los 20,16 M€ de préstamo en inversiones/capítulo 9 van en recuadros de previsión, explicadas, con el aviso de que solo se formalizará si es necesario según liquidación y ejecución, y que los remanentes de tesorería pueden reducirlo; el texto no afirma más de lo que dicen los datos.
- Antes de escribir código de gráficos, cargar la skill `dataviz`.
- Móvil primero (360 px sin scroll horizontal de página), contraste AA, gráficos con alternativa en tabla.

## Review Focus

1. Año inexistente (`?anio=1999`) o JSON que no carga (abierto por `file://`): mensaje claro en la página, nunca pantalla en blanco.
2. Búsqueda sin tildes ni mayúsculas («caritas» encuentra «Cáritas»).
3. Valores 2025 vacíos o 0: sin «NaN %» ni «Infinity %»; mostrar «nuevo en 2026».
4. Tablas anchas en móvil: scroll dentro de su contenedor, no de la página.
5. Importes negativos o cero (p. ej. «Pluri» sin importe) y partidas con nombre vacío: no rompen la tabla ni los totales.

## Estructura de ficheros

```
requirements.txt                 openpyxl, pytest
pytest.ini
tools/convert.py                 CLI: python tools/convert.py 2026
tools/budget/common.py           utilidades de lectura de celdas
tools/budget/labels.py           traducciones y agrupaciones en lenguaje llano
tools/budget/{resumen,ingresos,gastos,inversiones,subvenciones,deuda}.py
tools/tests/test_*.py            usan los Excel reales de 2026/
site/index.html (portada), resumen.html, ingresos.html, gastos.html,
     inversiones.html, subvenciones.html, deuda.html
site/css/styles.css
site/js/format.js (+ format.test.js), data.js, layout.js, charts.js,
     home.js, resumen.js, ingresos.js, gastos.js, inversiones.js, subvenciones.js, deuda.js
site/vendor/                     chart.js + README.md
site/data/index.json, site/data/2026/*.json
.github/workflows/pages.yml
README.md
```

## Contrato de datos (JSON en `site/data/<año>/`)

Importes en euros (número). `y2026` = previsión inicial del año; `y2025` = «créditos 2025»; `null` si el Excel no trae el dato.

- `site/data/index.json`: `{"anios":[{"anio":2026,"tipo":"inicial"}],"ultimo":2026}`
- `resumen.json`: `{anio, tipo, totalGastos, totalGastos2025, totalIngresos, gastosPorCapitulo:[Cap], ingresosPorCapitulo:[Cap], por100:[{bloque, caps:[int], importe, euros:int}]}` con `Cap = {cap:int, corto, oficial, y2025, y2026}`. `por100` suma exactamente 100 `euros` (método del resto mayor), bloques en este orden y con estos capítulos: «Obras e inversiones» [6,7], «Servicios» [2], «Personal» [1], «Otros» [3,4,5,8,9].
- `ingresos.json`: `{anio, capitulos:[{cap, corto, oficial, y2024, y2025, y2026, conceptos:[{codigo:str, nombre, y2024, y2025, y2026}]}]}`
- `gastos.json`: `{anio, capitulos:[Cap], programas:[{codigo:str, nombre, area:int, y2025, y2026}], areas:[{area:int, nombre}], partidas:[{cap:int, programa:str, codigo:str|null, nombre, y2025, y2026}]}`. En el capítulo 1 hay **una** partida por programa con `codigo:null` y `nombre:"Gastos de personal"`.
- `inversiones.json`: `{anio, total, fuentes:{prestamo, ingresosCorrientes, otros, rta, subvenciones}, programas:[{codigo, nombre, total, proyectos:[{nombre, partida:str, importe, prestamo, ingresosCorrientes, otros, rta, subvenciones}]}]}`
- `subvenciones.json`: `{anio, total2025, total2026, programas:[{partida, programa, credito, total2025, total2026, items:[{entidad, objeto, y2025, y2026}]}], entidades:[{entidad, total2025, total2026, programas:[str]}]}`
- `deuda.json`: `{anio, prestamos:[{fecha:"AAAA-MM-DD", entidad, importe, primeraAmortizacion, ultimaAmortizacion, tipoInteres, vivaInicio, vivaFin, amortizacion}], previsto:{fecha, importe, primeraAmortizacion, ultimaAmortizacion, tipoInteres}, serie:[{anio, viva}] (fin de cada año, solo préstamos existentes, desde 2022 hasta que llega a 0), titular:{vivaFin, vivaFinConPrevisto}, carga:{intereses, amortizacion, total, interesesConPrevisto}}`

---

### Task 1: Entorno Python y utilidades comunes

**Files:**
- Create: `requirements.txt`, `pytest.ini`, `tools/budget/__init__.py`, `tools/budget/common.py`, `tools/budget/labels.py`, `tools/tests/test_common.py`
- Modify: `.gitignore` (solo si falta algo)

**Interfaces:**
- Produces (`common.py`): `SRC_DIR(year:int)->Path` (`<raíz>/<año>/`); `find_file(year:int, prefix:str)->Path` (el único fichero de `SRC_DIR` cuyo nombre empieza por `prefix`, p. ej. `"A3"`); `load_sheet(path:Path, sheet:str)->Worksheet` (`data_only=True`); `num(v)->float|None` (None si no es número, redondeo a 2 decimales); `code_str(v)->str|None` (`112.0`→`"112"`, `"300.00"`→`"300.00"`, None→None); `sentence_case(text:str)->str` (pasa «IMPUESTO SOBRE BIENES» a «Impuesto sobre bienes»; conserva siglas de ≤4 letras en mayúscula como `IVA`, `ARU`, `ORA`, y no toca texto que ya tiene minúsculas); `largest_remainder(values:list[float], total:int=100)->list[int]`.
- Produces (`labels.py`): `CAPITULOS_GASTOS: dict[int, tuple[str,str]]` y `CAPITULOS_INGRESOS` ((corto en lenguaje llano, oficial)); `AREAS: dict[int,str]` (0 «Deuda», 1 «Servicios básicos (seguridad, limpieza, urbanismo…)», 2 «Protección social», 3 «Sanidad, educación, cultura y deporte», 4 «Economía y empleo», 9 «Administración general»); `BLOQUES_100: list[tuple[str, list[int]]]` según el contrato.

- [ ] **Step 1: Crear entorno**: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` con `openpyxl` y `pytest` (sin fijar versión: la última).
- [ ] **Step 2: Test `tools/tests/test_common.py`** con estas aserciones: `code_str(112.0)=="112"`; `code_str("300.00")=="300.00"`; `num("x") is None`; `sentence_case("IMPUESTO SOBRE EL IVA")=="Impuesto sobre el IVA"`; `sentence_case("Sueldos del Grupo C1")` sin cambios; `largest_remainder([37.84,33.64,24.29,4.22])==[38,34,24,4]`; `find_file(2026,"A3").name.startswith("A3")`.
- [ ] **Step 3: Verlo fallar** — `.venv/bin/pytest tools/tests/test_common.py -v` → FAIL (módulo no existe).
- [ ] **Step 4: Implementar** `common.py` y `labels.py` con las firmas de arriba. `labels.py` trae los 9 capítulos de gastos y los 9 de ingresos con nombre llano (p. ej. gastos 2 → «Servicios y mantenimiento» / «Gastos corrientes en bienes y servicios»; 6 → «Obras e inversiones» / «Inversiones reales»; 9 → «Devolución de préstamos» / «Pasivos financieros»; ingresos 1 → «Impuestos directos» con explicación en `oficial`).
- [ ] **Step 5: Pasa** — mismo comando → PASS.
- [ ] **Step 6: Commit** — `git add requirements.txt pytest.ini tools .gitignore && git commit -m "feat: utilidades comunes del conversor"`.

### Task 2: Conversor de Resumen (A1)

**Files:** Create `tools/budget/resumen.py`, `tools/tests/test_resumen.py`

**Interfaces:**
- Consumes: `common.find_file/load_sheet/num`, `labels.*`.
- Produces: `parse_resumen(year:int)->dict` con la forma de `resumen.json`.

- [ ] **Step 1: Test** con estas aserciones sobre `parse_resumen(2026)`: `totalGastos==64280861.35` (±0,01); `totalIngresos==64280861.35`; `totalGastos2025==65078315.2`; capítulo 1 de gastos `y2026==15616598.5`, `y2025==15562398.5`; capítulo 6 `y2026==24206942.85`; capítulo 1 de ingresos `y2026==16600000`; capítulo 9 de ingresos `y2026==20161623.64`; `[b["euros"] for b in por100]==[38,34,24,4]` con nombres `["Obras e inversiones","Servicios","Personal","Otros"]`; importe del bloque «Obras e inversiones» `==24326942.85`; ningún valor del JSON es `#REF!` ni NaN.
- [ ] **Step 2: Fallar**; **Step 3: Implementar** leyendo la hoja «2026» de `A1` (filas de gastos antes de «ESTADO DE INGRESOS»; columnas CAP., DESCRIPCIÓN, PREVISIONES 2026, CRÉDITOS 2025; ignorar columnas de trabajo y `#REF!`); **Step 4: Pasar**; **Step 5: Commit** `feat: conversor de resumen`.

### Task 3: Conversor de Ingresos (A2)

**Files:** Create `tools/budget/ingresos.py`, `tools/tests/test_ingresos.py`

**Interfaces:** Produces `parse_ingresos(year:int)->dict` (forma de `ingresos.json`).

- [ ] **Step 1: Test** sobre `parse_ingresos(2026)`: 9 capítulos; cap. 1 `y2026==16600000`, `y2025==15820000`, `y2024==14678000`; el concepto `"113"` del cap. 1 se llama «Impuesto sobre bienes inmuebles de naturaleza urbana» (sentence_case) con `y2026==11675000`; la suma de `conceptos` de cada capítulo ≈ total del capítulo (±1 €) para los capítulos 1 a 9; cap. 9 `y2026==20161623.64`.
- [ ] **Step 2–4:** Fallar, implementar, pasar. Reglas: cabecera de capítulo = fila con «CAPÍTULO …» en col. C; concepto = fila con código en col. B (numérico o texto) y nombre en col. C; saltar filas «ARTÍCULO …» y «TOTAL …» (el total sale del propio «TOTAL CAPÍTULO»); códigos con `code_str`.
- [ ] **Step 5: Commit** `feat: conversor de ingresos`.

### Task 4: Conversor de Gastos (A3)

**Files:** Create `tools/budget/gastos.py`, `tools/tests/test_gastos.py`

**Interfaces:** Produces `parse_gastos(year:int)->dict` (forma de `gastos.json`; `area = int(codigo[0])`).

- [ ] **Step 1: Test** sobre `parse_gastos(2026)`: totales de capítulo `y2026` — I `15616598.5`, II `21623640`, III `184000`, IV `1929680`, V `50000`, VI `24206942.85`, VII `120000`, VIII `15000`, IX `535000`; suma de `partidas` de cada capítulo == total del capítulo (±1 €); en el cap. 1 **no** hay partida con `codigo` distinto de `None` y el programa `"1300"` suma `177175`, el `"1320"` suma `2494600`; en el cap. 6 el programa `"1320"` tiene partidas `"622"` (`110000`) y `"624"` (`45000`); todo programa tiene `nombre` no vacío y `area`; `{p["area"] for p in programas}` ⊆ `{0,1,2,3,4,9}`.
- [ ] **Step 2–4:** Fallar, implementar, pasar. Reglas del Excel: bloque por capítulo con cabecera «CAPÍTULO …» (col. D); cabecera de programa = col. B numérica + nombre en col. D + «2025/2026» en E/F; partida = col. C con código (str) + nombre en col. D + importes E (2025) y F (2026); fila de subtotal de programa = col. B numérica sin nombre (ignorar); «TOTAL CAPÍTULO …» fija el total del capítulo. El nombre de un programa se toma de su primera cabecera en cualquier capítulo. Capítulo I: sumar las partidas de cada programa en una sola partida (`codigo:null`). Ignorar la hoja «Liberaciones…».
- [ ] **Step 5: Commit** `feat: conversor de gastos`.

### Task 5: Conversor de Inversiones (A9)

**Files:** Create `tools/budget/inversiones.py`, `tools/tests/test_inversiones.py`

**Interfaces:** Produces `parse_inversiones(year:int)->dict` (forma de `inversiones.json`).

- [ ] **Step 1: Test** sobre `parse_inversiones(2026)`: `total==24206942.85`; `fuentes` — `prestamo==20161623.64`, `ingresosCorrientes==2416188.11`, `otros==0`, `rta==183530.15`, `subvenciones==1445600.95` (±0,01); programa `"1320"` `total==155000` con proyectos «Cámaras de seguridad y tráfico» (60000, `prestamo==60000`, partida `"622"`), «Redacción planta baja edificio» (50000) y «Adquisición furgoneta» (45000, partida `"624"`); programa `"1330"` proyecto «Mejora de semáforos y señalética» con `ingresosCorrientes==30000` y `prestamo==0`; suma de `total` de programas == `total`; no aparece ningún nombre que contenga `"!!!"`.
- [ ] **Step 2–4:** Fallar, implementar, pasar. Hoja «2026». Columnas: C nombre, D importe, E préstamo, F ingresos corrientes, G otros, H RTA, I subvenciones, J total. Programa = col. B con código de 4 dígitos + nombre en C; partida = col. B con código de 3 dígitos; proyecto = fila con nombre en C e importe en D; saltar subtotales (col. C numérica). Parar en la fila «TOTAL CAPÍTULO VI» (ignorar NextGenerationEU y plurianuales). Valores vacíos = 0. Descartar textos de notas de trabajo (`!!!`, `Pluri??`).
- [ ] **Step 5: Commit** `feat: conversor de inversiones`.

### Task 6: Conversor de Subvenciones (A12)

**Files:** Create `tools/budget/subvenciones.py`, `tools/tests/test_subvenciones.py`

**Interfaces:** Produces `parse_subvenciones(year:int)->dict` (forma de `subvenciones.json`). `entidades` agrupa por nombre sin tildes ni mayúsculas (clave interna) y conserva el nombre más frecuente.

- [ ] **Step 1: Test** sobre `parse_subvenciones(2026)`: programa de partida `"2311 489.00"` contiene la entidad «Cruz Roja» con `y2025==10000` y `y2026==10000`; «Cáritas» tiene `y2026==3000`; «Club Deportivo Espeleoduero» `y2026==2000`; `total2026` == suma de `total2026` de programas == suma de `y2026` de `entidades`; `programa` en lenguaje normal (sentence_case, «Asistencia social primaria»); ninguna entidad vacía.
- [ ] **Step 2–4:** Fallar, implementar, pasar. Reglas: cabecera = col. B con partida (texto), col. C crédito, col. D programa; beneficiaria = col. D con nombre, E objeto, F 2025, G 2026; saltar filas de subtotal (col. D vacía).
- [ ] **Step 5: Commit** `feat: conversor de subvenciones`.

### Task 7: Conversor de Deuda y carga financiera (A13.1, A13.2)

**Files:** Create `tools/budget/deuda.py`, `tools/tests/test_deuda.py`

**Interfaces:** Produces `parse_deuda(year:int)->dict` (forma de `deuda.json`) y `project_balance(importe:float, amortizacion_anual:float, hasta:str, anio:int, viva_fin_anio_base:float, anio_base:int)->float` (saldo a 31/12/`anio` si se sigue amortizando la cuota constante, mínimo 0).

- [ ] **Step 1: Test** sobre `parse_deuda(2026)`: 3 préstamos (Bankia 2017, Unicaja 2018, Caja Laboral 2021) con `vivaInicio` 63442.59 / 615487.39 / 2034463.79 y `vivaFin` 27189.75 / 410324.95 / 1743826.11; `previsto.importe==11000000`, `previsto.fecha=="2026-03-01"`, `previsto.ultimaAmortizacion=="2037-12-31"`; `serie` por año — 2022: 4309552.67, 2023: 3777499.71, 2024: 3245446.74, 2025: 2713393.77, 2026: 2181340.81 (±0,01), 2027 ≈ 1658350.94 (±1), 2028 ≈ 1162550.75 (±1), último año de la serie 2032 con `viva==0`; `titular.vivaFin==2181340.81` y `titular.vivaFinConPrevisto==13181340.81`; `carga.intereses≈65378.59`, `carga.amortizacion≈532052.98`, `carga.interesesConPrevisto≈355709.37`. Test de `project_balance`: Caja Laboral, 290637.68 anuales hasta 2032-12-31 → saldo 2032 == 0.
- [ ] **Step 2–4:** Fallar, implementar, pasar. Los años 2022–2026 salen de las columnas de deuda viva de A13.1; los años siguientes se calculan con la cuota constante de cada préstamo hasta su última amortización (el saldo del último año vale 0). Intereses variables: no se calculan, se guarda el texto de `tipoInteres`. Carga 2026 = filas «TOTAL INTERESES 2026» / «TOTAL AMORTIZACIÓN 2026» de A13.2 (las dos apariciones: sin y con préstamo previsto).
- [ ] **Step 5: Commit** `feat: conversor de deuda`.

### Task 8: CLI, comprobación de cuadre y datos generados

**Files:** Create `tools/convert.py`, `tools/tests/test_convert.py`, `site/data/index.json`, `site/data/2026/*.json` (generados)

**Interfaces:**
- Consumes: todos los `parse_*`.
- Produces: `check_totals(data:dict[str,dict])->list[str]` (avisos; vacío si todo cuadra: capítulos de `gastos` y `ingresos` contra `resumen`, `inversiones.total` contra capítulo 6, ±1 €); `convert(year:int, out_dir:Path)->list[str]` (escribe los 6 JSON con `ensure_ascii=False, indent=1` y actualiza `index.json` sin duplicar el año; devuelve avisos). `python tools/convert.py 2026` imprime los avisos y sale con código 0.

- [ ] **Step 1: Test:** `convert(2026, tmp_path)` crea `resumen.json … deuda.json` e `index.json` con `{"anios":[{"anio":2026,"tipo":"inicial"}],"ultimo":2026}`; devuelve `[]`; `check_totals` con un dato manipulado (gastos cap. 2 +500 €) devuelve un aviso que menciona «capítulo 2»; ejecutar `convert` dos veces no duplica el año.
- [ ] **Step 2–4:** Fallar, implementar, pasar.
- [ ] **Step 5:** `.venv/bin/python tools/convert.py 2026` → genera `site/data/` en el repo; abrir los JSON y comprobar a ojo que no hay `NaN`, `#REF!` ni nombres vacíos.
- [ ] **Step 6: Commit** `feat: CLI de conversión y datos 2026`.

### Task 9: Base del sitio: estilos, utilidades, Chart.js, estructura de página

**Files:** Create `site/css/styles.css`, `site/js/format.js`, `site/js/format.test.js`, `site/js/data.js`, `site/js/layout.js`, `site/js/charts.js`, `site/vendor/*`, `site/vendor/README.md`

**Interfaces:**
- Produces (`format.js`): `formatEuros(n:number|null, opts?:{compact?:boolean}):string` (`1234567.8`→«1.234.568 €»; compacto «1,2 M€»; `null`→«—»); `formatVariation(curr:number|null, prev:number|null):{text:string, dir:"up"|"down"|"flat"|"new"|"na"}` (`prev` 0/null y `curr`>0 → `new` con «nuevo en 2026»; ambos null → `na`; sin NaN/Infinity); `normalize(text:string):string` (minúsculas sin tildes); `matches(text:string, query:string):boolean` (`normalize(text).includes(normalize(query))`); `sumBy(items, fn):number`.
- Produces (`data.js`): `getYear():Promise<number>` (de `?anio=`, si no `index.json.ultimo`; año no listado → lanza `Error("Año no disponible")`); `loadData(anio:number, name:string):Promise<object>` (`fetch("data/<anio>/<name>.json")`, error legible si falla).
- Produces (`layout.js`): `renderShell(active:string):Promise<{anio:number, main:HTMLElement}>` — pinta cabecera (nombre del sitio, selector de año que recarga con `?anio=`, menú: Inicio, Resumen, Ingresos, Gastos, Inversiones, Subvenciones, Deuda), pie con la fuente («Presupuesto inicial, Ayuntamiento de Aranda de Duero») y captura errores mostrándolos en `main` como aviso claro (Review Focus 1, incluido `file://`: «Abre la web desde un servidor, no haciendo doble clic en el fichero»).
- Produces (`charts.js`): `PALETTE` (azul, ámbar, rojo, celeste, marrón, gris, en ese orden) y `barChart/doughnutChart/lineChart(canvas, config)` finos sobre Chart.js con fuente, colores y formato de euros comunes.

- [ ] **Step 1: Descargar Chart.js** — `npm view chart.js version`; en un directorio temporal (no en el repo) `npm pack chart.js`, extraer, copiar el UMD de `dist/` y la licencia a `site/vendor/`; escribir `site/vendor/README.md` con versión, fecha y origen. Si la última versión no incluye UMD, usar su build ESM con `<script type="module">`.
- [ ] **Step 2: Test `format.test.js`** (`node --test site/js/`): `formatEuros(1234567.8)==="1.234.568 €"`; `formatEuros(null)==="—"`; `formatVariation(110,100)` → `dir:"up"`, `text` contiene «10 %»; `formatVariation(50,0).dir==="new"`; `formatVariation(null,null).dir==="na"`; `matches("Asoc. Cáritas","CARITAS")===true`.
- [ ] **Step 3: Fallar** (`node --test site/js/`), **Step 4: implementar** `format.js`, **Step 5: pasar**.
- [ ] **Step 6:** Escribir `styles.css` con las variables de color de «Global Constraints», tipografía del sistema, tarjetas, tablas con contenedor `overflow-x:auto`, cabecera roja con texto blanco, foco visible, modo móvil primero. Implementar `data.js`, `layout.js`, `charts.js` según las firmas.
- [ ] **Step 7: Verificar** — `python3 -m http.server -d site 8000`; con una página de prueba mínima ver cabecera, selector de año y, con `?anio=1999`, el aviso «Año no disponible».
- [ ] **Step 8: Commit** `feat: base del sitio (estilos, utilidades, Chart.js)`.

### Task 10: Portada

**Files:** Create `site/index.html`, `site/js/home.js`

**Interfaces:** Consumes `renderShell("inicio")`, `loadData(anio,"resumen")`, `formatEuros`, `formatVariation`, `charts.PALETTE`.

- [ ] **Step 1:** Contenido, en este orden: titular «Por cada 100 € que gasta el Ayuntamiento en {anio}…»; barra horizontal dividida con los 4 bloques de `por100` (colores azul, ámbar, rojo, gris; etiqueta con importe por cada 100 € y, al seleccionar, el importe total y los capítulos incluidos explicados en una frase); frase con el total (`totalGastos`) y la variación frente a 2025; cuatro tarjetas de acceso (Ingresos «de dónde sale», Inversiones «obras», Subvenciones «a quién», Deuda «cuánto se debe»); enlace «Ver el detalle de gastos». Cada bloque es un botón/enlace accesible por teclado y hay una tabla equivalente visible (`<details>` «Ver como tabla»).
- [ ] **Step 2: Verificar en navegador** (servidor local; también a 360 px de ancho): se ve «38 €», «34 €», «24 €», «4 €» (por ese orden), total «64.280.861 €» y la variación «-1 %» frente a 2025; sin scroll horizontal de página; texto blanco solo sobre fondos permitidos.
- [ ] **Step 3: Commit** `feat: portada`.

### Task 11: Gastos y Resumen

**Files:** Create `site/gastos.html`, `site/js/gastos.js`, `site/resumen.html`, `site/js/resumen.js`

**Interfaces:** Consumes `gastos.json`, `resumen.json`, `matches`, `formatEuros`, `formatVariation`.

- [ ] **Step 1 (gastos):** Selector «Ver por: ¿En qué se gasta? (programa) / ¿Qué tipo de gasto es? (capítulo)». Por programa: áreas (`areas`) → programas → partidas; por capítulo: capítulos → programas → partidas. Cada nivel es una lista de barras horizontales proporcionales (HTML/CSS) con importe, % del total y variación frente a 2025; al pulsar se despliega el siguiente nivel; el capítulo 1 muestra solo el total por programa con la nota «Los sueldos se muestran agrupados por programa». Buscador por texto (sobre programas y partidas, con `matches`) que muestra una tabla plana de resultados. Nombre oficial en `title`/detalle.
- [ ] **Step 2 (resumen):** Dos barras apiladas «De dónde sale» (ingresos por capítulo) y «En qué se gasta» (gastos por capítulo), ambas de 64.280.861 €, y una tabla debajo con comparación 2025.
- [ ] **Step 3: Verificar:** en gastos, «Servicios básicos» → «Seguridad» → partidas; en capítulo 1 sin partidas de sueldos; buscar «semaforos» devuelve resultados sin escribir tildes; resumen: ambas barras suman 64.280.861 €.
- [ ] **Step 4: Commit** `feat: gastos y resumen`.

### Task 12: Ingresos

**Files:** Create `site/ingresos.html`, `site/js/ingresos.js`

- [ ] **Step 1:** Rosca/barras de ingresos por capítulo con nombres llanos (Impuestos directos, etc.) y texto «Esto son los impuestos que pagan los vecinos» cuando aplica; al pulsar un capítulo, lista de conceptos con 2024, 2025, 2026 y variación; buscador por concepto. Valores nulos o 0 sin «NaN %» (Review Focus 3).
- [ ] **Step 2: Verificar:** capítulo 1 muestra 16.600.000 €, «Impuesto sobre bienes inmuebles de naturaleza urbana» 11.675.000 €; concepto sin dato 2024 muestra «nuevo en 2026» o «—», nunca NaN.
- [ ] **Step 3: Commit** `feat: ingresos`.

### Task 13: Inversiones

**Files:** Create `site/inversiones.html`, `site/js/inversiones.js`

- [ ] **Step 1:** Cabecera con total (24.206.943 €) y barra de fuentes de financiación (préstamo, ingresos corrientes, otros, remanente, subvenciones) con la leyenda en lenguaje llano; recuadro de aviso sobre remanentes (texto de «Global Constraints», sin afirmar más que los datos); lista por programa con sus proyectos; cada proyecto muestra su importe y una mini-barra de financiación con tooltip; enlace al recuadro de deuda.
- [ ] **Step 2: Verificar:** total y fuentes coinciden con Task 5 (préstamo 20.161.624 €); programa «Seguridad» muestra 155.000 € con «Adquisición furgoneta» 45.000 €; sin textos `!!!`.
- [ ] **Step 3: Commit** `feat: inversiones`.

### Task 14: Subvenciones

**Files:** Create `site/subvenciones.html`, `site/js/subvenciones.js`

- [ ] **Step 1:** Dos vistas con pestañas: «Por actividad» (programas con total y entidades dentro; objeto del convenio, 2025, 2026, diferencia) y «Por entidad» (buscador `matches` + lista de entidades con total 2026/2025 y programas en los que aparece). Total general arriba.
- [ ] **Step 2: Verificar:** buscar «caritas» muestra «Cáritas» con 3.000 €; «Cruz Roja» 10.000 €; el total de la pestaña «Por entidad» coincide con el de «Por actividad».
- [ ] **Step 3: Commit** `feat: subvenciones`.

### Task 15: Deuda

**Files:** Create `site/deuda.html`, `site/js/deuda.js`

- [ ] **Step 1:** Titular «Deuda a 31/12/{anio}: 2.181.341 €» (solo préstamos existentes) con frase de comparación con el inicio de año; gráfico de línea/barras `serie` (años reales y previsión en tono distinto, solo préstamos existentes); tabla de préstamos (fecha de concesión, entidad, importe, tipo de interés, última amortización, lo que queda a 31/12/{anio}); bloque «Carga financiera» (intereses + amortización del año, sin y con previsto); **recuadro destacado «Previsión»**: préstamo de 11 M€ (fecha, años) y los 20,16 M€ de préstamo de las inversiones, explicando la diferencia sin afirmar más de lo que dicen los datos, con la frase de que solo se formalizará si es necesario y que los remanentes pueden reducirlo; el recuadro no entra en el gráfico.
- [ ] **Step 2: Verificar:** titular 2.181.341 €; gráfico cae a 0 en 2032; el recuadro muestra «11 M€» y «20,16 M€»; el gráfico no incluye el préstamo previsto.
- [ ] **Step 3: Commit** `feat: deuda`.

### Task 16: Publicación en GitHub Pages, README y revisión final

**Files:** Create `.github/workflows/pages.yml`, `README.md`; Modify `.gitignore` (si hace falta)

- [ ] **Step 1:** Workflow en push a `main`: `actions/checkout`, `actions/configure-pages`, `actions/upload-pages-artifact` con `path: site`, `actions/deploy-pages` (permisos `pages: write`, `id-token: write`; usar las últimas versiones mayores). Sin paso de build.
- [ ] **Step 2:** `README.md`: qué es, cómo regenerar datos (`python tools/convert.py 2026`), cómo añadir un año (carpeta `AAAA/` con los mismos Excel, ejecutar, commit), cómo previsualizar (`python3 -m http.server -d site`), y los pasos manuales en GitHub: *Settings → Pages → Source: GitHub Actions*.
- [ ] **Step 3: Verificación completa:** `.venv/bin/pytest -q` y `node --test site/js/` en verde; recorrer las 7 páginas en navegador a 1280 px y 360 px; sin errores en consola; sin scroll horizontal de página; todas las rutas relativas (probar sirviendo `site/` desde una subcarpeta: `mkdir /tmp/x && ln -s $PWD/site /tmp/x/visorpresupuesto && python3 -m http.server -d /tmp/x` y abrir `/visorpresupuesto/`).
- [ ] **Step 4: Commit** `feat: despliegue en GitHub Pages y documentación`.

---

## Self-review

- **Cobertura del diseño:** portada (T10), año (T9, T8), secciones resumen/ingresos/gastos/inversiones/subvenciones/deuda (T11–T15), capítulo 1 agrupado (T4, T11), deuda con previsión fuera del gráfico y dos cifras (T7, T15), remanentes (T13, T15), colores y vendor (T9), Pages (T16), avisos de cuadre (T8), hoja «2026» de A9 (T5).
- **Consistencia de tipos:** `Cap`, `por100`, `serie`, `titular` y `carga` definidos en el contrato y usados con los mismos nombres en conversor y páginas.
- **Proporción:** los pasos de implementación fijan firma, reglas del Excel y valores esperados; los cuerpos los escribe quien implementa.
