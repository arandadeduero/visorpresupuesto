import { runPage, esc } from "./layout.js";
import { formatEuros } from "./format.js";
import { filaHtml, variacionHtml, tablaHtml } from "./ui.js";

function bloque(titulo, capitulos, total) {
  const max = Math.max(...capitulos.map((c) => c.y2026));
  const ordenados = [...capitulos].sort((a, b) => b.y2026 - a.y2026);
  return `<section><h2>${esc(titulo)}</h2>
    <ul class="barras">${ordenados.map((c) => `<li>${filaHtml({
      nombre: c.corto,
      title: `Nombre oficial: ${c.oficial}`,
      importe: c.y2026,
      max,
      extra: `${((c.y2026 / total) * 100).toLocaleString("es-ES", { maximumFractionDigits: 1 })} % del total · ${variacionHtml(c.y2026, c.y2025)}`,
    })}</li>`).join("")}</ul></section>`;
}

runPage("resumen", async ({ anio, main, load }) => {
  const r = await load("resumen");
  const prestamos = r.ingresosPorCapitulo.find((c) => c.cap === 9).y2026;
  const filas = (caps) => caps.map((c) => `<tr><td>${esc(c.corto)}</td><td class="num">${formatEuros(c.y2025)}</td><td class="num">${formatEuros(c.y2026)}</td></tr>`);
  const cab = [{ texto: "Concepto" }, { texto: `${anio - 1}`, num: true }, { texto: `${anio}`, num: true }];

  main.innerHTML = `
    <h1>Resumen del presupuesto ${anio}</h1>
    <p class="lead">El Ayuntamiento prevé ingresar <strong>${formatEuros(r.totalIngresos)}</strong> y gastar <strong>${formatEuros(r.totalGastos)}</strong>: el presupuesto está equilibrado.</p>
    <div class="aviso"><h3>Una aclaración sobre los ingresos</h3>
      <p>De los ingresos previstos, <strong>${formatEuros(prestamos)}</strong> son préstamos que se podrían pedir para pagar inversiones. No es dinero que ya se tenga: se explica en las páginas de <a href="inversiones.html?anio=${anio}">inversiones</a> y de <a href="deuda.html?anio=${anio}">deuda</a>.</p></div>
    ${bloque("De dónde sale el dinero", r.ingresosPorCapitulo, r.totalIngresos)}
    ${bloque("En qué se gasta", r.gastosPorCapitulo, r.totalGastos)}
    <details><summary>Ver como tablas</summary>
      <h3>Ingresos</h3>${tablaHtml(cab, filas(r.ingresosPorCapitulo))}
      <h3>Gastos</h3>${tablaHtml(cab, filas(r.gastosPorCapitulo))}
    </details>
    <p class="muted">La cifra de ${anio - 1} son los créditos del presupuesto de ${anio - 1}.</p>`;
});
