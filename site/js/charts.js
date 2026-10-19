// Gráficos con Chart.js (cargado como script global desde vendor/). Colores de la identidad municipal en orden fijo.
import { formatEuros } from "./format.js";

export const PALETTE = ["#0083c1", "#f5a800", "#ce0e2d", "#646464", "#3cb4e5", "#a4541c"];
export const TEXTO_SOBRE = { "#0083c1": "#fff", "#f5a800": "#3c3c3c", "#ce0e2d": "#fff", "#646464": "#fff", "#3cb4e5": "#3c3c3c", "#a4541c": "#fff" };

const base = () => {
  Chart.defaults.font.family = '"Outfit", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
  Chart.defaults.color = "#3c3c3c";
};

function crear(canvas, tipo, datos, opciones) {
  base();
  const grafico = new Chart(canvas, { type: tipo, data: datos, options: { responsive: true, maintainAspectRatio: false, ...opciones } });
  // La tipografía puede terminar de cargar después del primer dibujo: se redibuja para que los textos del gráfico usen Outfit.
  document.fonts?.ready.then(() => grafico.update("none"));
  return grafico;
}

// Marcas del eje: «0», «0,5 M€», «1 M€»… (siempre en millones a partir de 100.000 € para no mezclar unidades)
const marcaEuros = (v) => (v === 0 ? "0" : Math.abs(v) >= 100000 ? `${(v / 1e6).toLocaleString("es-ES", { maximumFractionDigits: 2 })}\u00a0M€` : formatEuros(v));

const tooltipEuros = { callbacks: { label: (c) => ` ${c.dataset.label ? c.dataset.label + ": " : ""}${formatEuros(c.parsed.y ?? c.parsed)}` } };

export function lineChart(canvas, { labels, datasets }) {
  return crear(canvas, "line", { labels, datasets }, {
    interaction: { mode: "index", intersect: false },
    plugins: { legend: { display: datasets.length > 1 }, tooltip: tooltipEuros },
    scales: { y: { beginAtZero: true, ticks: { callback: marcaEuros }, grid: { color: "#e9f4f9" } }, x: { grid: { display: false } } },
  });
}

export function barChart(canvas, { labels, datasets, horizontal = false }) {
  return crear(canvas, "bar", { labels, datasets }, {
    indexAxis: horizontal ? "y" : "x",
    plugins: { legend: { display: datasets.length > 1 }, tooltip: tooltipEuros },
    scales: { [horizontal ? "x" : "y"]: { beginAtZero: true, ticks: { callback: marcaEuros }, grid: { color: "#e9f4f9" } } },
  });
}

export function doughnutChart(canvas, { labels, values, colors = PALETTE, leyenda = true }) {
  return crear(canvas, "doughnut", { labels, datasets: [{ data: values, backgroundColor: colors, borderColor: "#fff", borderWidth: 2 }] }, {
    plugins: { legend: { display: leyenda, position: "bottom" }, tooltip: { callbacks: { label: (c) => ` ${c.label}: ${formatEuros(c.parsed)}` } } },
  });
}
