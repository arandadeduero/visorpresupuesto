# Presupuestos de Aranda de Duero

Web estática para que cualquier vecino entienda el presupuesto del Ayuntamiento: en qué se gasta el dinero, de dónde sale, qué obras se prevén, a quién se dan subvenciones y cuánto se debe.

Hoy incluye el **presupuesto inicial 2026** (previsiones, no gastos ya realizados).

## Cómo funciona

- `2026/` contiene los Excel oficiales del presupuesto.
- `tools/` convierte esos Excel en ficheros JSON (Python).
- `site/` es la web (HTML y JavaScript simples, sin framework). Lee los JSON de `site/data/` y dibuja los gráficos con Chart.js (guardado en `site/vendor/`, sin depender de ningún CDN).
- GitHub Actions publica solo la carpeta `site/` en GitHub Pages.

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
.venv/bin/python tools/convert.py 2026
```

El script avisa si algún total de los Excel no cuadra con el resumen (A1).

## Añadir otro año

1. Crear la carpeta `AAAA/` con los mismos Excel (nombres que empiezan por `A1`, `A2`, `A3`, `A9`, `A12`, `A13.1` y `A13.2`).
2. `.venv/bin/python tools/convert.py AAAA`
3. Revisar los avisos, hacer commit de `site/data/` y publicar.

El selector de año de la web lee `site/data/index.json`, que el script actualiza solo.

## Tests

```bash
.venv/bin/pytest          # conversor, con los Excel reales de 2026
node --test site/js/      # funciones de formato, búsqueda y árbol de gastos
```

## Publicar en GitHub Pages

Una sola vez, en el repositorio de GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**. A partir de ahí, cada push a `main` publica la web en `https://arandadeduero.github.io/visorpresupuesto/`.

## Actualizar Chart.js

```bash
npm pack chart.js     # descargar la última versión
# copiar dist/chart.umd.min.js y LICENSE.md a site/vendor/ y anotar la versión en site/vendor/README.md
```

## Notas de los datos

- Los totales salen de la hoja «2026» de `A1`. En `A9` (inversiones) se usa la hoja «2026», no «Copia de 2026».
- El préstamo previsto de 11 M€ (anexo de deuda) no entra en la deuda del titular ni en el gráfico: es una previsión que solo se formalizará si es necesario.
