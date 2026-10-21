// Gráfico de quesito (rosca) con el reparto de gastos o de ingresos, por capítulos (los grandes bloques)
// o por artículos (el nivel siguiente de la clasificación económica: «Préstamos recibidos», «Personal funcionario»…).
import { esc } from "./layout.js";
import { formatEuros, etiquetaCapitulo } from "./format.js";
import { doughnutChart } from "./charts.js";
import { tablaHtml } from "./ui.js";

// El color de cada capítulo (y de los tonos de sus artículos) vive en el CSS: --cap-N y --cap-N-tono-K en
// styles.css / escalas.css, con un valor para el tema claro y otro para el oscuro. Aquí solo se elige cuál:
// `clase` para pintar muestras en el HTML (.cap-N, .cap-N-tono-K) y `variable` para el lienzo de Chart.js.
export const claseCapitulo = (cap, tono = 0) => (tono ? `cap-${cap}-tono-${tono}` : `cap-${cap}`);
export const variableCapitulo = (cap, tono = 0) => `--cap-${cap}-tono-${tono}`;

/** Capítulos con importe > 0, de mayor a menor, con su porcentaje y color. */
export function datosQuesito(capitulos) {
  const con = capitulos.filter((c) => c.actual > 0);
  const total = con.reduce((s, c) => s + c.actual, 0);
  const items = con
    .map((c) => ({ cap: c.cap, nombre: etiquetaCapitulo(c), oficial: c.oficial, valor: c.actual, pct: (c.actual / total) * 100, clase: claseCapitulo(c.cap), variable: variableCapitulo(c.cap) }))
    .sort((a, b) => b.valor - a.valor);
  return { items, total };
}

// ---- Vista por artículos ----
// Hay unos 20 artículos: no se pueden distinguir por color solo. Cada artículo lleva el color de su capítulo
// (la misma familia que en la vista por capítulos) en distintos tonos, las porciones de un capítulo van juntas,
// los artículos pequeños se agrupan en «Otros artículos de <capítulo>» y la leyenda agrupada por capítulo da
// el nombre, el porcentaje y el importe de cada uno, así que el color nunca es la única pista.

export const UMBRAL_OTROS = 2; // % del total por debajo del cual un artículo se agrupa (si hay al menos dos así en su capítulo)

// Tonos de una familia (0 = el color del capítulo, 1-5 = más claro, más oscuro… según el tema, ver --tono-K en styles.css).
export const NUM_TONOS = 6;
export const tonoArticulo = (i) => i % NUM_TONOS;

/** Artículos de ingresos en una lista plana con su capítulo (en gastos ya vienen así en `articulos`). */
export const articulosDeIngresos = (datos) => datos.capitulos.flatMap((c) => c.articulos.map((a) => ({ ...a, cap: c.cap })));

/**
 * Porciones por artículo, agrupadas por capítulo (el capítulo mayor primero) y dentro de cada capítulo de mayor a menor.
 * Devuelve `items` (en el orden del gráfico), `grupos` (para la leyenda) y `total`.
 */
export function datosArticulos(capitulos, articulos) {
  const total = capitulos.reduce((s, c) => s + (c.actual > 0 ? c.actual : 0), 0);
  const grupos = capitulos
    .filter((c) => c.actual > 0)
    .map((c) => {
      const propios = articulos.filter((a) => a.cap === c.cap && a.actual > 0).sort((a, b) => b.actual - a.actual);
      const pequenos = propios.filter((a) => (a.actual / total) * 100 < UMBRAL_OTROS);
      // Solo se agrupa si hay al menos dos pequeños y queda algún artículo grande: «Otros artículos de X» no dice nada si lo es todo.
      const plegar = pequenos.length >= 2 && pequenos.length < propios.length;
      const grandes = plegar ? propios.filter((a) => !pequenos.includes(a)) : propios;
      const crudos = grandes.map((a) => ({ codigo: a.codigo, nombre: a.nombre, oficial: a.oficial, valor: a.actual, otros: false }));
      if (plegar) {
        crudos.push({
          codigo: pequenos.map((a) => a.codigo).join("+"),
          nombre: `Otros artículos del Cap ${c.cap}`,
          oficial: `Artículos ${pequenos.map((a) => a.codigo).join(", ")}: ${pequenos.map((a) => a.nombre).join("; ")}`,
          valor: pequenos.reduce((s, a) => s + a.actual, 0),
          otros: true,
        });
      }
      const items = crudos.map((x, i) => ({ ...x, cap: c.cap, pct: (x.valor / total) * 100, tono: tonoArticulo(i), clase: claseCapitulo(c.cap, tonoArticulo(i)), variable: variableCapitulo(c.cap, tonoArticulo(i)) }));
      return { cap: c.cap, nombre: etiquetaCapitulo(c), oficial: c.oficial, clase: claseCapitulo(c.cap), variable: variableCapitulo(c.cap), valor: c.actual, pct: (c.actual / total) * 100, items };
    })
    .filter((g) => g.items.length)
    .sort((a, b) => b.valor - a.valor);
  return { items: grupos.flatMap((g) => g.items), grupos, total };
}

const pct = (n) => n.toLocaleString("es-ES", { maximumFractionDigits: 1 });

const muestra = (clase) => `<i class="muestra ${clase}"></i>`;

/** Leyenda de capítulos como tabla con cabecera (se ordena al pulsar; por defecto, por la primera columna). */
export function tablaLeyendaCapitulos(items) {
  return tablaHtml(
    [{ texto: "Capítulo" }, { texto: "% del total", num: true }, { texto: "Importe", num: true }],
    items.map((i) => `<tr title="Nombre oficial: ${esc(i.oficial)}"><td>${muestra(i.clase)}${esc(i.nombre)}</td><td class="num">${pct(i.pct)} %</td><td class="num">${formatEuros(i.valor)}</td></tr>`),
  );
}

/** Leyenda de artículos como tabla plana: capítulo, artículo, % e importe (el capítulo va primero, así que por defecto quedan agrupados). */
export function tablaLeyendaArticulos(grupos) {
  const capitulo = new Map(grupos.map((g) => [g.cap, g.nombre]));
  const filas = grupos.flatMap((g) => g.items);
  return tablaHtml(
    [{ texto: "Capítulo" }, { texto: "Artículo" }, { texto: "% del total", num: true }, { texto: "Importe", num: true }],
    filas.map(
      (i) => `<tr title="${esc(i.otros ? i.oficial : "Nombre oficial: " + i.oficial)}"><td>${muestra(i.clase)}${esc(capitulo.get(i.cap))}</td><td>${esc(i.nombre)}</td><td class="num">${pct(i.pct)} %</td><td class="num">${formatEuros(i.valor)}</td></tr>`,
    ),
  );
}

let contador = 0;

/**
 * Pinta en `contenedor` un quesito con su leyenda (importe y porcentaje). Requiere Chart.js.
 * Con `articulos` (lista plana con `cap`) añade el selector «Ver por: Capítulos | Artículos»; por defecto, capítulos.
 */
export function pintaQuesito(contenedor, capitulos, titulo, articulos = null, vista = "capitulos") {
  const id = `quesito-${++contador}`;
  const porArticulos = vista === "articulos" && articulos;
  const datos = porArticulos ? datosArticulos(capitulos, articulos) : datosQuesito(capitulos);
  const { items, total } = datos;
  const resumen = items.slice(0, 3).map((i) => `${i.nombre} ${pct(i.pct)} %`).join(", ");
  const selector = articulos
    ? `<div class="controles controles-quesito"><span id="${id}-ver" class="etiqueta-ver">Ver por:</span>
      <div class="pestanas" role="group" aria-labelledby="${id}-ver">
        <button type="button" data-vista="capitulos" aria-pressed="${!porArticulos}">Capítulos</button>
        <button type="button" data-vista="articulos" aria-pressed="${Boolean(porArticulos)}">Artículos</button>
      </div></div>`
    : "";
  const ayuda = porArticulos
    ? `<p class="muted ayuda-vista">Cada capítulo (grande bloque) se divide en artículos, que son tipos de ingreso o de gasto más concretos. Cada capítulo mantiene su color en distintos tonos.</p>`
    : "";
  contenedor.innerHTML = `<figure class="quesito">
    <figcaption><strong>${esc(titulo)}</strong><br><span class="muted">Total ${formatEuros(total)}</span></figcaption>
    ${selector}${ayuda}
    <div class="quesito-grafico"><canvas role="img" aria-label="${esc(titulo)}, por ${porArticulos ? "artículos" : "capítulos"}: ${esc(resumen)}…"></canvas></div>
    ${porArticulos ? tablaLeyendaArticulos(datos.grupos) : tablaLeyendaCapitulos(items)}</figure>`;
  doughnutChart(contenedor.querySelector("canvas"), { labels: items.map((i) => i.nombre), values: items.map((i) => i.valor), colores: items.map((i) => i.variable), leyenda: false });
  contenedor.querySelectorAll("[data-vista]").forEach((b) =>
    b.addEventListener("click", () => {
      if (b.dataset.vista === (porArticulos ? "articulos" : "capitulos")) return;
      const grafico = Chart.getChart(contenedor.querySelector("canvas"));
      if (grafico) grafico.destroy();
      pintaQuesito(contenedor, capitulos, titulo, articulos, b.dataset.vista);
      contenedor.querySelector(`[data-vista="${b.dataset.vista}"]`).focus();
    }),
  );
}
