import { runPage, esc, tarjetasHtml, nombreTipo, tipoDe, documentosOficialesHtml } from "./layout.js";
import { formatEuros, formatPct, formatVariation, sumBy } from "./format.js";
import { claseCrece } from "./escalas.js";
import { destacar, porHabitante } from "./insights.js";
import { variacionHtml } from "./ui.js";
import { urlPagina } from "./rutas.js";

const EXPLICACION = {
  "Obras e inversiones": "Obras nuevas y mejoras en calles, edificios e instalaciones, y ayudas para inversiones.",
  Servicios: "El funcionamiento diario de la ciudad: limpieza, luz, agua, mantenimiento, contratos y material.",
  Personal: "Sueldos y cotizaciones de las personas que trabajan en el Ayuntamiento.",
  Otros: "Intereses y devolución de préstamos, ayudas a entidades y un fondo para imprevistos.",
};

function comparacion(total, anterior, anio) {
  if (anterior === null || anterior === undefined) return ""; // el presupuesto no trae el año anterior
  const v = formatVariation(total, anterior);
  const pct = v.text.slice(1).replace(" %", "&nbsp;%"); // que el «%» no salte de línea
  if (v.dir === "up") return `un ${pct} más que en ${anio - 1}`;
  if (v.dir === "down") return `un ${pct} menos que en ${anio - 1}`;
  return `igual que en ${anio - 1}`;
}

runPage("inicio", async ({ anio, indice, main, load }) => {
  const r = await load("resumen"); // gastos.json (el más pesado) solo se pide después, para la tarjeta «¿Cuánto gasta…?»
  const cambio = comparacion(r.totalGastos, r.totalGastosAnterior, anio);
  const porVecino = formatEuros(porHabitante(r.totalGastos, r.habitantes));
  const suma = sumBy(r.por100, (b) => b.euros);
  const segmentos = r.por100.map((b, i) => {
    return `<button class="seg serie-${i + 1} ${claseCrece(b.euros, suma)}" type="button" data-i="${i}" aria-pressed="false">
      <span class="seg-euros">${b.euros}&nbsp;€</span><span class="seg-nombre">${esc(b.bloque)}</span></button>`;
  }).join("");
  const filas = r.por100.map((b) => `<tr><td>${esc(b.bloque)}</td><td class="num">${b.euros} €</td><td class="num">${formatEuros(b.importe)}</td></tr>`).join("");

  main.innerHTML = `
    <p class="antetitulo">${esc(nombreTipo(tipoDe(indice, anio)))} · ${anio}</p>
    <p class="cifra-portada">${formatEuros(r.totalGastos, { compact: true })}</p>
    <p class="entrada-portada">Es lo que el Ayuntamiento de Aranda de Duero prevé gastar en ${anio}: <strong>${porVecino} por habitante</strong>${cambio ? `, ${cambio}` : ""}.</p>
    <h1 class="titulo-reparto">Por cada 100&nbsp;€ que gasta el Ayuntamiento en ${anio}…</h1>
    <div class="stackbar" role="group" aria-label="Reparto de cada 100 euros">${segmentos}</div>
    <p class="detalle-seg" id="detalle-seg" aria-live="polite"></p>
    <details><summary>Ver como tabla</summary>
      <div class="tabla-scroll"><table class="datos"><thead><tr><th>En qué</th><th class="num">Por cada 100 €</th><th class="num">Importe</th></tr></thead><tbody>${filas}</tbody></table></div>
    </details>
    <p><a href="${urlPagina("gastos", anio)}">Ver el detalle de los gastos del Ayuntamiento por política</a></p>
    <section class="destacado" aria-labelledby="titulo-destacado">
      <h2 id="titulo-destacado">¿Cuánto gasta Aranda de Duero en…?</h2>
      <div id="destacado" class="destacado-caja" aria-live="polite"><p class="muted">Cargando…</p></div>
      <button class="boton" type="button" id="otra" disabled>Enséñame otra</button>
    </section>
    <h2>Y además…</h2>
    ${tarjetasHtml(anio)}
    <p class="muted">Es el ${nombreTipo(tipoDe(indice, anio))}: lo que el Ayuntamiento prevé gastar (${formatEuros(r.totalGastos)}), no lo gastado hasta hoy. El importe por habitante es ese gasto dividido entre la población (${r.habitantes.toLocaleString("es-ES")} habitantes; ${esc(r.fuentePoblacion)}). No es lo que paga cada vecino: ni los impuestos se reparten por igual ni todo el gasto se paga con ellos.</p>
    ${documentosOficialesHtml(indice, anio)}`;

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
          <div><span class="cifra">${formatPct(d.pct)}</span><span>del presupuesto</span></div>
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
