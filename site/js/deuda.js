import { runPage, esc } from "./layout.js";
import { formatEuros } from "./format.js";
import { PALETTE, barChart } from "./charts.js";
import { tablaHtml } from "./ui.js";
import { explicaDosPrestamos } from "./deuda-texto.js";

const fecha = (iso) => iso.split("-").reverse().join("/");
const mes = (iso) => new Date(`${iso}T12:00:00`).toLocaleDateString("es-ES", { month: "long", year: "numeric" });

runPage("deuda", async ({ anio, main, load }) => {
  const [d, inv] = await Promise.all([load("deuda"), load("inversiones")]);
  const vivaInicio = d.prestamos.reduce((s, p) => s + p.vivaInicio, 0);
  const prestamoInversiones = inv.fuentes.prestamo;
  const pv = d.previsto;
  const real = PALETTE[0];
  const prevision = PALETTE[4];

  main.innerHTML = `
    <h1>Deuda del Ayuntamiento <span class="muted">${anio}</span></h1>
    <p class="cifra">${formatEuros(d.titular.vivaFin)}</p>
    <p class="lead">es lo que el Ayuntamiento deberá a los bancos a 31 de diciembre de ${anio}, con los préstamos que ya tiene. A 1 de enero era de ${formatEuros(vivaInicio)}: durante el año devuelve ${formatEuros(d.carga.amortizacion)}.</p>

    <div class="aviso"><h3>Previsión: un préstamo nuevo de ${formatEuros(pv.importe, { compact: true })}</h3>
      <p>El presupuesto prevé un préstamo de <strong>${formatEuros(pv.importe)}</strong> para ${esc(mes(pv.fecha))}, que se empezaría a devolver en ${esc(mes(pv.primeraAmortizacion))} y terminaría en ${esc(mes(pv.ultimaAmortizacion))} (${esc(pv.tipoInteres)}). Si se firmara, la deuda a 31 de diciembre de ${anio} sería de <strong>${formatEuros(d.titular.vivaFinConPrevisto)}</strong>.</p>
      <p><strong>Solo se formalizará si es necesario</strong>, según la liquidación y la ejecución del presupuesto.</p>
      <p>${esc(explicaDosPrestamos(pv.importe, prestamoInversiones))} Por eso el gráfico de abajo no las incluye. Las cifras de préstamo en las <a href="inversiones.html?anio=${anio}">inversiones</a> se explican en esa página.</p></div>

    <h2>Cómo evoluciona la deuda actual</h2>
    <p class="muted">Solo con los préstamos que ya existen. Cada columna es lo que se debe a 31 de diciembre.</p>
    <div class="grafico"><canvas id="grafico" role="img" aria-label="Deuda a 31 de diciembre de cada año: baja desde ${formatEuros(d.serie[0].viva)} en ${d.serie[0].anio} hasta cero en ${d.serie.at(-1).anio}"></canvas></div>
    <ul class="leyenda"><li><i style="background:${real}"></i>Deuda a final de año (años cerrados)</li><li><i style="background:${prevision}"></i>Previsión con los préstamos actuales</li></ul>
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
    <p class="muted">Si se firmara el préstamo previsto, los intereses de ${anio} subirían a ${formatEuros(d.carga.interesesConPrevisto)} (estimación; los tipos son variables y se calculan con previsiones de Euribor).</p>`;

  const colores = d.serie.map((s) => (s.anio < anio ? real : prevision));
  barChart(main.querySelector("#grafico"), {
    labels: d.serie.map((s) => String(s.anio)),
    datasets: [{ label: "Deuda a 31 de diciembre", data: d.serie.map((s) => s.viva), backgroundColor: colores, borderRadius: 4 }],
  });
});
