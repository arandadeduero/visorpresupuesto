import { runPage, esc } from "./layout.js";
import { formatEuros } from "./format.js";
import { barChart, colorPorPunto } from "./charts.js";
import { tablaHtml } from "./ui.js";
import { fecha, avisoPrevisto, avisoSinPrevisto } from "./deuda-texto.js";

runPage("deuda", async ({ anio, main, load }) => {
  const [d, inv] = await Promise.all([load("deuda"), load("inversiones")]);
  const vivaInicio = d.prestamos.reduce((s, p) => s + p.vivaInicio, 0);
  const prestamoInversiones = inv.fuentes.prestamo;
  const pv = d.previsto;
  // Años cerrados en azul (--serie-1) y previsión en celeste (--serie-5)
  const real = "--serie-1";
  const prevision = "--serie-5";

  main.innerHTML = `
    <h1>Deuda del Ayuntamiento <span class="muted">${anio}</span></h1>
    <p class="cifra">${formatEuros(d.titular.vivaFin)}</p>
    <p class="lead">es lo que el Ayuntamiento deberá a los bancos a 31 de diciembre de ${anio}, con los préstamos que ya tiene. A 1 de enero era de ${formatEuros(vivaInicio)}: durante el año devuelve ${formatEuros(d.carga.amortizacion)}.</p>

    ${pv ? avisoPrevisto(pv, d, prestamoInversiones, anio) : avisoSinPrevisto(prestamoInversiones, anio)}

    <h2>Cómo evoluciona la deuda actual</h2>
    <p class="muted">Solo con los préstamos que ya existen. Cada columna es lo que se debe a 31 de diciembre.</p>
    <div class="grafico"><canvas id="grafico" role="img" aria-label="Deuda a 31 de diciembre de cada año: baja desde ${formatEuros(d.serie[0].viva)} en ${d.serie[0].anio} hasta cero en ${d.serie.at(-1).anio}"></canvas></div>
    <ul class="leyenda"><li><i class="serie-1"></i>Deuda a final de año (años cerrados)</li><li><i class="serie-5"></i>Previsión con los préstamos actuales</li></ul>
    <details><summary>Ver como tabla</summary>${tablaHtml([{ texto: "Final de año" }, { texto: "Deuda", num: true }], d.serie.map((s) => `<tr><td>${s.anio}</td><td class="num">${formatEuros(s.viva)}</td></tr>`))}</details>

    <h2>Los préstamos actuales</h2>
    ${tablaHtml(
      [{ texto: "Concedido" }, { texto: "Entidad" }, { texto: "Importe pedido", num: true }, { texto: "Interés" }, { texto: "Se termina de pagar" }, { texto: `Queda por pagar a 31/12/${anio}`, num: true }],
      d.prestamos.map((p) => `<tr><td>${fecha(p.fecha)}</td><td>${esc(p.entidad)}</td><td class="num">${formatEuros(p.importe)}</td><td>${esc(p.tipoInteres)}</td><td>${fecha(p.ultimaAmortizacion)}</td><td class="num">${formatEuros(p.vivaFin)}</td></tr>`).concat(
        `<tr><th colspan="2">Total</th><th class="num">${formatEuros(d.prestamos.reduce((s, p) => s + p.importe, 0))}</th><th></th><th></th><th class="num">${formatEuros(d.titular.vivaFin)}</th></tr>`,
      ),
    )}

    <h2>Cuánto cuesta la deuda en ${anio}</h2>
    <p>La carga financiera es lo que se paga cada año por los préstamos: <strong>${formatEuros(d.carga.total)}</strong> en total, de los cuales ${formatEuros(d.carga.amortizacion)} son devolución del dinero prestado y ${formatEuros(d.carga.intereses)} son intereses.</p>
    ${d.carga.interesesConPrevisto === null ? `<p class="muted">Los tipos de interés son variables y el anexo los calcula con previsiones de Euribor.</p>` : `<p class="muted">Si se firmara el préstamo previsto, los intereses de ${anio} subirían a ${formatEuros(d.carga.interesesConPrevisto)} (estimación; los tipos son variables y se calculan con previsiones de Euribor).</p>`}`;

  const colores = d.serie.map((s) => (s.anio < anio ? real : prevision));
  barChart(main.querySelector("#grafico"), {
    labels: d.serie.map((s) => String(s.anio)),
    datasets: [{ label: "Deuda a 31 de diciembre", data: d.serie.map((s) => s.viva), backgroundColor: colorPorPunto(colores), borderRadius: 4 }],
  });
});
