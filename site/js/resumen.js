import { runPage, esc } from "./layout.js";
import { formatEuros, etiquetaCapitulo } from "./format.js";
import { filaHtml, variacionHtml, tablaHtml, delTotal } from "./ui.js";
import { urlPagina } from "./rutas.js";
import { pintaQuesito, articulosDeIngresos } from "./quesito.js";
import { mayoresCambios } from "./insights.js";

function cambios(titulo, items, clase) {
  const lista = items
    .map((x) => `<li><span>${esc(x.nombre)}</span><strong class="${clase === "sube" ? "var-up" : "var-down"}">${clase === "sube" ? "▲ +" : "▼ −"}${formatEuros(Math.abs(x.delta))}</strong><small class="muted">${x.pct === null ? "nuevo este año" : `${x.pct > 0 ? "+" : "−"}${Math.abs(x.pct).toLocaleString("es-ES", { maximumFractionDigits: 0 })} %`}</small></li>`)
    .join("");
  return `<section><h3>${esc(titulo)}</h3><ol class="cambios">${lista || "<li>Sin cambios</li>"}</ol></section>`;
}

function bloque(titulo, capitulos, total) {
  const max = Math.max(...capitulos.map((c) => c.actual));
  const ordenados = [...capitulos].sort((a, b) => b.actual - a.actual);
  return `<section><h2>${esc(titulo)}</h2>
    <ul class="barras">${ordenados.map((c) => `<li>${filaHtml({
      nombre: etiquetaCapitulo(c),
      title: `Nombre oficial: ${c.oficial}`,
      importe: c.actual,
      max,
      extra: `${delTotal(c.actual, total)}${c.anterior === null || c.anterior === undefined ? "" : ` · ${variacionHtml(c.actual, c.anterior)}`}`, // sin año anterior en el resumen: no se compara
    })}</li>`).join("")}</ul></section>`;
}

runPage("resumen", async ({ anio, main, load }) => {
  const [r, gastos, ingresos] = await Promise.all([load("resumen"), load("gastos"), load("ingresos")]);
  const prestamos = r.ingresosPorCapitulo.find((c) => c.cap === 9)?.actual ?? 0;
  const equilibrado = Math.abs(r.totalIngresos - r.totalGastos) < 1;
  // Las políticas con inversiones no se comparan en los años en que el Excel no trae las inversiones del año anterior.
  const comparables = gastos.politicas.filter((p) => p.anterior !== null && p.anterior !== undefined);
  const gc = mayoresCambios(comparables, 5);
  const sinComparar = gastos.politicas.length - comparables.length;
  const conceptos = ingresos.capitulos.flatMap((c) => c.conceptos);
  // Si el estado de ingresos no trae ninguna cifra del año anterior, «nuevo» no significa nada: no se listan
  const ingresosComparables = conceptos.some((x) => x.anterior !== null && x.anterior !== undefined);
  const ic = mayoresCambios(conceptos, 5);
  const suben = { g: gc.suben, i: ic.suben };
  const bajan = { g: gc.bajan, i: ic.bajan };
  const conAnterior = r.totalGastosAnterior !== null && r.totalGastosAnterior !== undefined; // algunos presupuestos antiguos no traen el año anterior
  const filas = (caps) => caps.map((c) => `<tr><td>${esc(etiquetaCapitulo(c))}</td>${conAnterior ? `<td class="num">${formatEuros(c.anterior)}</td>` : ""}<td class="num">${formatEuros(c.actual)}</td></tr>`);
  const cab = [{ texto: "Concepto" }, ...(conAnterior ? [{ texto: `${anio - 1}`, num: true }] : []), { texto: `${anio}`, num: true }];
  const comparacion = conAnterior ? `
    <h2>Qué ha cambiado más respecto a ${anio - 1}</h2>
    <p class="muted">Diferencia en euros entre el presupuesto de ${anio} y los créditos de ${anio - 1}.${sinComparar ? ` No se comparan ${sinComparar} políticas de gasto con inversiones, porque el presupuesto de ${anio} no trae las inversiones de ${anio - 1}.` : ""}</p>
    <div class="dos-columnas">
      ${cambios("Gastos que más suben", suben.g, "sube")}${cambios("Gastos que más bajan", bajan.g, "baja")}
      ${ingresosComparables ? `${cambios("Ingresos que más suben", suben.i, "sube")}${cambios("Ingresos que más bajan", bajan.i, "baja")}` : ""}
    </div>
    ${ingresosComparables ? "" : `<p class="muted">El estado de ingresos de ${anio} no trae las cifras de ${anio - 1} concepto a concepto, así que los ingresos no se comparan.</p>`}` : `
    <p class="muted">El presupuesto de ${anio} no trae las cifras de ${anio - 1}, así que aquí no se compara con el año anterior.</p>`;

  main.innerHTML = `
    <h1>Resumen del presupuesto ${anio}</h1>
    <p class="lead">El Ayuntamiento prevé ingresar <strong>${formatEuros(r.totalIngresos)}</strong> y gastar <strong>${formatEuros(r.totalGastos)}</strong>${equilibrado ? ": el presupuesto está equilibrado" : ""}.</p>
    ${(r.notas ?? []).map((n) => `<div class="aviso"><h3>Una diferencia que viene en los documentos oficiales</h3><p>${esc(n)}</p></div>`).join("")}
    ${prestamos > 0 ? `<div class="aviso"><h3>Una aclaración sobre los ingresos</h3>
      <p>De los ingresos previstos, <strong>${formatEuros(prestamos)}</strong> son préstamos que se podrían pedir para pagar inversiones. No es dinero que ya se tenga: se explica en las páginas de <a href="${urlPagina("inversiones", anio)}">inversiones</a> y de <a href="${urlPagina("deuda", anio)}">deuda</a>.</p></div>` : ""}
    <div class="dos-columnas"><div id="q-ingresos"></div><div id="q-gastos"></div></div>
    ${bloque("De dónde sale el dinero", r.ingresosPorCapitulo, r.totalIngresos)}
    ${bloque("En qué se gasta", r.gastosPorCapitulo, r.totalGastos)}
    ${comparacion}
    <details><summary>Ver como tablas</summary>
      <h3>Ingresos</h3>${tablaHtml(cab, filas(r.ingresosPorCapitulo))}
      <h3>Gastos</h3>${tablaHtml(cab, filas(r.gastosPorCapitulo))}
    </details>
    ${conAnterior ? `<p class="muted">La cifra de ${anio - 1} son los créditos del presupuesto de ${anio - 1}.</p>` : ""}`;

  pintaQuesito(main.querySelector("#q-ingresos"), r.ingresosPorCapitulo, "De dónde sale el dinero", articulosDeIngresos(ingresos));
  pintaQuesito(main.querySelector("#q-gastos"), r.gastosPorCapitulo, "En qué se gasta", gastos.articulos);
});
