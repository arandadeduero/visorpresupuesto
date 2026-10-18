import { runPage, esc } from "./layout.js";
import { formatEuros, formatVariation } from "./format.js";
import { PALETTE, TEXTO_SOBRE } from "./charts.js";

const EXPLICACION = {
  "Obras e inversiones": "Obras nuevas y mejoras en calles, edificios e instalaciones, y ayudas para inversiones.",
  Servicios: "El funcionamiento diario de la ciudad: limpieza, luz, agua, mantenimiento, contratos y material.",
  Personal: "Sueldos y cotizaciones de las personas que trabajan en el Ayuntamiento.",
  Otros: "Intereses y devolución de préstamos, ayudas a entidades y un fondo para imprevistos.",
};

function comparacion(total, anterior, anio) {
  const v = formatVariation(total, anterior);
  if (v.dir === "up") return `un ${v.text.slice(1)} más que en ${anio - 1}`;
  if (v.dir === "down") return `un ${v.text.slice(1)} menos que en ${anio - 1}`;
  return `igual que en ${anio - 1}`;
}

runPage("inicio", async ({ anio, main, load }) => {
  const r = await load("resumen");
  const consulta = `?anio=${anio}`;
  const segmentos = r.por100.map((b, i) => {
    const color = PALETTE[i];
    return `<button class="seg" type="button" data-i="${i}" aria-pressed="false" style="flex-grow:${b.euros};background:${color};color:${TEXTO_SOBRE[color]}">
      <span class="seg-euros">${b.euros}&nbsp;€</span><span class="seg-nombre">${esc(b.bloque)}</span></button>`;
  }).join("");
  const filas = r.por100.map((b) => `<tr><td>${esc(b.bloque)}</td><td class="num">${b.euros} €</td><td class="num">${formatEuros(b.importe)}</td></tr>`).join("");

  main.innerHTML = `
    <h1>Por cada 100&nbsp;€ que gasta el Ayuntamiento en ${anio}…</h1>
    <div class="stackbar" role="group" aria-label="Reparto de cada 100 euros">${segmentos}</div>
    <p class="detalle-seg" id="detalle-seg" aria-live="polite"></p>
    <p class="lead">Total previsto: <strong>${formatEuros(r.totalGastos)}</strong>, ${comparacion(r.totalGastos, r.totalGastos2025, anio)}.</p>
    <details><summary>Ver como tabla</summary>
      <div class="tabla-scroll"><table class="datos"><thead><tr><th>En qué</th><th class="num">Por cada 100 €</th><th class="num">Importe</th></tr></thead><tbody>${filas}</tbody></table></div>
    </details>
    <p><a href="gastos.html${consulta}">Ver el detalle de los gastos →</a></p>
    <h2>Y además…</h2>
    <div class="cards">
      <a class="card" href="ingresos.html${consulta}"><strong>Ingresos</strong><span>De dónde sale el dinero</span></a>
      <a class="card" href="inversiones.html${consulta}"><strong>Inversiones</strong><span>Las obras previstas y cómo se pagan</span></a>
      <a class="card" href="subvenciones.html${consulta}"><strong>Subvenciones</strong><span>A qué entidades se da dinero</span></a>
      <a class="card" href="deuda.html${consulta}"><strong>Deuda</strong><span>Cuánto se debe y cuándo se paga</span></a>
    </div>
    <p class="muted">Es el presupuesto inicial: lo que el Ayuntamiento prevé gastar, no lo gastado hasta hoy.</p>`;

  const detalle = main.querySelector("#detalle-seg");
  const botones = [...main.querySelectorAll(".seg")];
  const elegir = (i) => {
    const b = r.por100[i];
    botones.forEach((btn, j) => btn.setAttribute("aria-pressed", String(i === j)));
    const pct = Math.round((b.importe / r.totalGastos) * 1000) / 10;
    detalle.innerHTML = `<strong>${esc(b.bloque)}:</strong> ${formatEuros(b.importe)} (${String(pct).replace(".", ",")} % del total). ${esc(EXPLICACION[b.bloque] ?? "")}`;
  };
  botones.forEach((btn, i) => btn.addEventListener("click", () => elegir(i)));
  elegir(0);
});
