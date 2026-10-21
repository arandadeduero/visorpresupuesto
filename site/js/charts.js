// Gráficos con Chart.js (cargado como script global desde vendor/). Los colores salen de las variables CSS del tema
// (claro u oscuro, el que tenga el sistema) mediante opciones «scriptable»: se vuelven a leer en cada dibujo, y al
// cambiar el esquema del sistema todos los gráficos se repintan con los colores del nuevo tema.
import { formatEuros } from "./format.js";
import { colorVar, alCambiarEsquema } from "./colores.js";

/** Series de la identidad municipal, en orden fijo (variables de styles.css). */
export const SERIES = ["--serie-1", "--serie-2", "--serie-3", "--serie-4", "--serie-5", "--serie-6"];

/** Color de cada punto/barra/porción: `vars` es una lista de nombres de variable, o un solo nombre para todos. */
export const colorPorPunto = (vars) => (c) => colorVar(Array.isArray(vars) ? vars[c.dataIndex % vars.length] : vars);

const texto = () => colorVar("--grafico-texto");
const rejilla = () => colorVar("--grafico-rejilla");

const base = () => {
  Chart.defaults.font.family = '"Outfit", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
  Chart.defaults.color = texto;
};

const leyendaTema = (display, extra = {}) => ({ display, labels: { color: texto }, ...extra });
const tooltipTema = (callbacks) => ({
  callbacks,
  backgroundColor: () => colorVar("--tooltip-fondo"),
  titleColor: () => colorVar("--tooltip-texto"),
  bodyColor: () => colorVar("--tooltip-texto"),
  borderColor: rejilla,
  borderWidth: 1,
});
const ejeTema = (extra = {}) => ({ beginAtZero: true, ticks: { callback: marcaEuros, color: texto }, grid: { color: rejilla }, border: { color: rejilla }, ...extra });

function crear(canvas, tipo, datos, opciones) {
  base();
  const grafico = new Chart(canvas, { type: tipo, data: datos, options: { responsive: true, maintainAspectRatio: false, ...opciones } });
  // La tipografía puede terminar de cargar después del primer dibujo: se redibuja para que los textos del gráfico usen Outfit.
  document.fonts?.ready.then(() => grafico.update("none"));
  return grafico;
}

// Cambio de esquema del sistema: los gráficos vivos se repintan con los colores del nuevo tema.
alCambiarEsquema(() => {
  if (typeof Chart === "undefined") return;
  Object.values(Chart.instances).forEach((g) => g.update("none"));
});

// Marcas del eje: «0», «0,5 M€», «1 M€»… (siempre en millones a partir de 100.000 € para no mezclar unidades)
const marcaEuros = (v) => (v === 0 ? "0" : Math.abs(v) >= 100000 ? `${(v / 1e6).toLocaleString("es-ES", { maximumFractionDigits: 2 })} M€` : formatEuros(v));

const tooltipEuros = () => tooltipTema({ label: (c) => ` ${c.dataset.label ? c.dataset.label + ": " : ""}${formatEuros(c.parsed.y ?? c.parsed)}` });

export function lineChart(canvas, { labels, datasets }) {
  return crear(canvas, "line", { labels, datasets }, {
    interaction: { mode: "index", intersect: false },
    plugins: { legend: leyendaTema(datasets.length > 1), tooltip: tooltipEuros() },
    scales: { y: ejeTema(), x: { ticks: { color: texto }, grid: { display: false }, border: { color: rejilla } } },
  });
}

export function barChart(canvas, { labels, datasets, horizontal = false }) {
  return crear(canvas, "bar", { labels, datasets }, {
    indexAxis: horizontal ? "y" : "x",
    plugins: { legend: leyendaTema(datasets.length > 1), tooltip: tooltipEuros() },
    scales: horizontal
      ? { x: ejeTema(), y: { ticks: { color: texto }, grid: { display: false }, border: { color: rejilla } } }
      : { y: ejeTema(), x: { ticks: { color: texto }, grid: { display: false }, border: { color: rejilla } } },
  });
}

/** `colores`: lista de nombres de variable CSS (`--cap-1`, `--serie-3`…), una por porción. */
export function doughnutChart(canvas, { labels, values, colores = SERIES, leyenda = true }) {
  return crear(canvas, "doughnut", { labels, datasets: [{ data: values, backgroundColor: colorPorPunto(colores), borderColor: () => colorVar("--grafico-borde"), borderWidth: 2 }] }, {
    plugins: { legend: leyendaTema(leyenda, { position: "bottom" }), tooltip: tooltipTema({ label: (c) => ` ${c.label}: ${formatEuros(c.parsed)}` }) },
  });
}
