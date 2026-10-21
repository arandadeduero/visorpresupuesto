import { runPage, esc, tarjetasHtml } from "./layout.js";
import { formatEuros, formatVariation } from "./format.js";
import { claseCrece } from "./escalas.js";
import { destacar, porHabitante } from "./insights.js";
import { variacionHtml } from "./ui.js";

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
  const r = await load("resumen"); // gastos.json (el más pesado) solo se pide después, para la tarjeta «¿Cuánto gasta…?»
  const porVecino = formatEuros(porHabitante(r.totalGastos, r.habitantes));
  const consulta = `?anio=${anio}`;
  const suma = r.por100.reduce((s, b) => s + b.euros, 0);
  const segmentos = r.por100.map((b, i) => {
    return `<button class="seg serie-${i + 1} ${claseCrece(b.euros, suma)}" type="button" data-i="${i}" aria-pressed="false">
      <span class="seg-euros">${b.euros}&nbsp;€</span><span class="seg-nombre">${esc(b.bloque)}</span></button>`;
  }).join("");
  const filas = r.por100.map((b) => `<tr><td>${esc(b.bloque)}</td><td class="num">${b.euros} €</td><td class="num">${formatEuros(b.importe)}</td></tr>`).join("");

  main.innerHTML = `
    <h1>Por cada 100&nbsp;€ que gasta el Ayuntamiento en ${anio}…</h1>
    <div class="stackbar" role="group" aria-label="Reparto de cada 100 euros">${segmentos}</div>
    <p class="detalle-seg" id="detalle-seg" aria-live="polite"></p>
    <p class="lead">Total previsto: <strong>${formatEuros(r.totalGastos)}</strong>, ${comparacion(r.totalGastos, r.totalGastosAnterior, anio)}.</p>
    <details><summary>Ver como tabla</summary>
      <div class="tabla-scroll"><table class="datos"><thead><tr><th>En qué</th><th class="num">Por cada 100 €</th><th class="num">Importe</th></tr></thead><tbody>${filas}</tbody></table></div>
    </details>
    <p><a href="gastos.html${consulta}">Ver el detalle de los gastos del Ayuntamiento por política</a></p>
    <section class="destacado" aria-labelledby="titulo-destacado">
      <h2 id="titulo-destacado">¿Cuánto gasta Aranda de Duero en…?</h2>
      <div id="destacado" class="destacado-caja" aria-live="polite"><p class="muted">Cargando…</p></div>
      <button class="boton" type="button" id="otra" disabled>Enséñame otra</button>
    </section>
    <h2>Para cada vecino</h2>
    <p class="lead">El presupuesto equivale a unos <strong>${porVecino}</strong> por habitante al año (${r.habitantes.toLocaleString("es-ES")} habitantes).</p>
    <p class="muted">Es el gasto previsto del Ayuntamiento dividido entre la población (${esc(r.fuentePoblacion)}). No es lo que paga cada vecino: ni los impuestos se reparten por igual ni todo el gasto se paga con ellos.</p>
    <h2>Y además…</h2>
    ${tarjetasHtml(anio)}
    <p class="muted">Es el presupuesto inicial: lo que el Ayuntamiento prevé gastar, no lo gastado hasta hoy.</p>`;

  const detalle = main.querySelector("#detalle-seg");
  const botones = [...main.querySelectorAll(".seg")];
  const elegir = (i) => {
    const b = r.por100[i];
    botones.forEach((btn, j) => btn.setAttribute("aria-pressed", String(i === j)));
    const pct = Math.round((b.importe / r.totalGastos) * 1000) / 10;
    detalle.innerHTML = `<strong>${esc(b.bloque)}:</strong> ${formatEuros(b.importe)} (${String(pct).replace(".", ",")} % del total). ${esc(EXPLICACION[b.bloque] ?? "")} <span class="muted">(${b.caps.length > 1 ? "Capítulos" : "Capítulo"} ${b.caps.join(", ")})</span>`;
  };
  botones.forEach((btn, i) => btn.addEventListener("click", () => elegir(i)));
  elegir(0);

  // «¿Cuánto gasta Aranda de Duero en…?»: una política de gasto cada vez, en orden aleatorio.
  // Se pinta lo demás primero y gastos.json se baja después: no bloquea la parte visible de la portada.
  const caja = main.querySelector("#destacado");
  const otra = main.querySelector("#otra");
  try {
    const gastos = await load("gastos");
    const orden = [...gastos.politicas].filter((p) => p.actual > 0).sort(() => Math.random() - 0.5);
    let actual = 0;
    const mostrar = () => {
      const d = destacar(orden[actual], r.totalGastos, r.habitantes);
      caja.innerHTML = `<p class="destacado-nombre">${esc(d.nombre)}</p>
        <div class="cifras">
          <div><span class="cifra">${formatEuros(d.porHabitante)}</span><span>por habitante</span></div>
          <div><span class="cifra">${formatEuros(d.importe, { compact: true })}</span><span>en total</span></div>
          <div><span class="cifra">${d.pct.toLocaleString("es-ES", { maximumFractionDigits: 1 })} %</span><span>del presupuesto</span></div>
        </div>
        ${d.anterior == null ? "" : `<p class="muted">${variacionHtml(d.importe, d.anterior)}</p>`}`;
    };
    otra.addEventListener("click", () => {
      actual = (actual + 1) % orden.length;
      mostrar();
    });
    mostrar();
    otra.disabled = false;
  } catch {
    main.querySelector(".destacado").hidden = true; // sin esa tarjeta la portada sigue siendo útil
  }
});
