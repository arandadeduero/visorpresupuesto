// Gráfico de quesito (rosca) con el reparto por capítulos de gastos o de ingresos.
import { esc } from "./layout.js";
import { formatEuros } from "./format.js";
import { doughnutChart } from "./charts.js";

// Un color fijo por capítulo, el mismo en todas las páginas (los tres primeros coinciden con la portada:
// obras e inversiones azul, servicios ámbar, personal rojo). Los dos últimos son tonos claros de la paleta municipal.
export const COLOR_CAPITULO = {
  1: "#ce0e2d",
  2: "#f5a800",
  3: "#646464",
  4: "#3cb4e5",
  5: "#a4541c",
  6: "#0083c1",
  7: "#3c3c3c",
  8: "#8fc9e6",
  9: "#f9d37a",
};

/** Capítulos con importe > 0, de mayor a menor, con su porcentaje y color. */
export function datosQuesito(capitulos) {
  const con = capitulos.filter((c) => c.actual > 0);
  const total = con.reduce((s, c) => s + c.actual, 0);
  const items = con
    .map((c) => ({ cap: c.cap, nombre: c.corto, oficial: c.oficial, valor: c.actual, pct: (c.actual / total) * 100, color: COLOR_CAPITULO[c.cap] }))
    .sort((a, b) => b.valor - a.valor);
  return { items, total };
}

const pct = (n) => n.toLocaleString("es-ES", { maximumFractionDigits: 1 });

/** Pinta en `contenedor` un quesito con su leyenda (importe y porcentaje de cada capítulo). Requiere Chart.js. */
export function pintaQuesito(contenedor, capitulos, titulo) {
  const { items, total } = datosQuesito(capitulos);
  const resumen = items.slice(0, 3).map((i) => `${i.nombre} ${pct(i.pct)} %`).join(", ");
  contenedor.innerHTML = `<figure class="quesito">
    <figcaption><strong>${esc(titulo)}</strong><br><span class="muted">Total ${formatEuros(total)}</span></figcaption>
    <div class="quesito-grafico"><canvas role="img" aria-label="${esc(titulo)}: ${esc(resumen)}…"></canvas></div>
    <ul class="leyenda leyenda-quesito">${items
      .map((i) => `<li title="Nombre oficial: ${esc(i.oficial)}"><i style="background:${i.color}"></i><span>${esc(i.nombre)}</span> <strong>${pct(i.pct)} %</strong> <span class="muted">${formatEuros(i.valor)}</span></li>`)
      .join("")}</ul></figure>`;
  doughnutChart(contenedor.querySelector("canvas"), { labels: items.map((i) => i.nombre), values: items.map((i) => i.valor), colors: items.map((i) => i.color), leyenda: false });
}
