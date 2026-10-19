# Presupuestos de Aranda de Duero

**🌐 Web: <https://presupuestos.arandadeduero.dev/>**

Visor de los presupuestos del Ayuntamiento de Aranda de Duero pensado para cualquier vecino, sin necesidad de saber de presupuestos: en qué se gasta el dinero, de dónde sale, qué obras se prevén, a quién se dan subvenciones y cuánto se debe.

Incluye los **presupuestos iniciales 2024, 2025 y 2026** (previsiones, no gastos ya realizados); por defecto se muestra el último y hay un selector de año.

## Qué se puede ver

| Página | Qué responde |
|---|---|
| **Inicio** | «Por cada 100 € que gasta el Ayuntamiento…», euros por habitante y una tarjeta «¿Cuánto gasta Aranda de Duero en…?» |
| **Resumen** | Ingresos frente a gastos, gráficos de quesito por capítulo y qué ha cambiado más respecto al año anterior |
| **Ingresos** | De dónde sale el dinero, por capítulo y concepto, con buscador |
| **Gastos** | En qué se gasta, por política (cultura, deporte…) o por tipo de gasto, hasta la partida (el personal, agrupado por programa) |
| **Inversiones** | Obras y compras previstas y cómo se financia cada una |
| **Subvenciones** | A qué entidades se da dinero, por actividad y por entidad |
| **Deuda** | Préstamos actuales, deuda por año, coste anual y la previsión de un préstamo nuevo |
| **Indicadores** | Ahorro bruto, deuda por habitante, impuestos y tasas por habitante… |
| **Comparar** | Dos presupuestos a elegir, frente a frente: barras pareadas por política o capítulo, tabla, frases, indicadores, por habitante y evolución |
| **Calculadora** | «¿A qué se destina lo que pago?»: reparto orientativo de tus impuestos y tasas |
| **Guía** | Qué significan las palabras del presupuesto |
| **Descargas** | Los datos en JSON y los Excel originales |

Los gráficos usan los colores del Ayuntamiento, la web funciona bien en el móvil y todo importe procede de los Excel oficiales (no se inventa ningún dato).

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
2. Añadir la población de ese año en `tools/budget/labels.py` (`POBLACION`).
3. `.venv/bin/python tools/convert.py AAAA`
4. Revisar los avisos, hacer commit de `site/data/` y publicar.

El selector de año de la web lee `site/data/index.json`, que el script actualiza solo.

**Claves de los JSON.** Son las mismas en todos los años: `actual` es el importe del año del presupuesto y `anterior` el del año anterior (`anterior2` el de hace dos años en ingresos, solo si el Excel lo trae). `total`/`totalAnterior` en subvenciones y `totalGastosAnterior` en el resumen siguen la misma idea. El conversor localiza las columnas por sus rótulos, no por su posición, porque cambian de un ejercicio a otro.

**Diferencias entre ejercicios** (detalle en el documento de diseño): 2024 no tiene préstamo previsto en el anexo de deuda (`previsto`, `vivaFinConPrevisto` e `interesesConPrevisto` valen `null` y la web no muestra esas cajas); en 2025 el Excel trae 250.000 € más de ingresos que de gastos (es una nota, no un aviso); en 2024 y 2025 el Excel de gastos no trae las inversiones del año anterior, así que esas partidas, programas y políticas quedan sin variación (`null`, `sinAnterior`).

## Tests

```bash
.venv/bin/pytest                      # conversor y comprobaciones de la web, con los Excel reales
node --test "site/js/*.test.js"       # formato, búsqueda, árbol de gastos, indicadores y calculadora
```

## Publicación y comprobaciones automáticas

- **En cada Pull Request** (`.github/workflows/ci.yml`): `pytest`, comprobación de que los JSON de `site/data/` están al día y cuadran con los Excel, y tests de JavaScript.
- **En cada push a `main`** (`.github/workflows/pages.yml`): se repiten los tests y, solo si pasan, se publica `site/` en GitHub Pages. Al final, el propio workflow comprueba que la web publicada carga.
- La web se sirve en <https://presupuestos.arandadeduero.dev/> (dominio configurado en *Settings → Pages*, con origen «GitHub Actions»).

## Actualizar Chart.js

```bash
npm pack chart.js     # descargar la última versión
# copiar dist/chart.umd.min.js y LICENSE.md a site/vendor/ y anotar la versión en site/vendor/README.md
```

## Notas sobre los datos

- Los totales salen de la hoja «<año>» de `A1`. En `A9` (inversiones) y `A12` se usa la hoja «<año>», no las «Copia de…» ni las hojas de trabajo.
- El préstamo previsto de 11 M€ (anexo de deuda de 2025 y 2026) no entra en la deuda del titular ni en el gráfico: es una previsión que solo se formalizará si es necesario. La web muestra también los 20,16 M€ de préstamo de la financiación de inversiones, sin afirmar la causa de la diferencia.
- Los importes «por habitante» dividen el gasto entre la población del INE (INE: 33.757 habitantes en 2024, 33.956 en 2025; 2026 usa el dato de 2025, el último disponible); no son lo que paga cada vecino.
- Ideas tomadas de otros visores (Gobierto Presupuestos, visor de Fuengirola): ver el apartado correspondiente del diseño. Para comparar con otros municipios: [Gobierto Presupuestos](https://presupuestos.gobierto.es/municipios/aranda-de-duero).

## Licencia

[MIT](LICENSE) © 2026 Ayuntamiento de Aranda de Duero. Chart.js tiene su propia licencia (MIT), en `site/vendor/`.
