import { runPage, esc } from "./layout.js";
import { formatEuros } from "./format.js";
import { calcularIndicadores } from "./lecturas.js";

const p1 = (n) => (n === null ? "—" : `${n.toLocaleString("es-ES", { maximumFractionDigits: 1 })} %`);

runPage("indicadores", async ({ anio, main, load }) => {
  const [resumen, ingresos, deuda] = await Promise.all([load("resumen"), load("ingresos"), load("deuda")]);
  const i = calcularIndicadores({ resumen, ingresos, deuda });
  const tarjetas = [
    {
      titulo: "Impuestos y tasas por habitante",
      valor: formatEuros(i.impuestosYTasasPorHabitante),
      texto: `Lo que el Ayuntamiento prevé recaudar de media por habitante con impuestos (${formatEuros(i.impuestosPorHabitante)}) y tasas. No es lo que paga cada vecino: depende de su vivienda, vehículos y servicios.`,
    },
    {
      titulo: "Ahorro bruto",
      valor: formatEuros(i.ahorroBruto, { compact: true }),
      texto: `Lo que queda de los ingresos de cada año (${p1(i.ahorroBrutoPct)} de ${formatEuros(i.ingresosCorrientes, { compact: true })}) después de pagar sueldos, servicios y ayudas, sin contar los intereses. Sirve para pagar la deuda y para invertir. Cuanto mayor, más margen.`,
    },
    {
      titulo: "Deuda por habitante",
      valor: formatEuros(i.deudaPorHabitante),
      texto: `Con los préstamos que ya existen, a 31 de diciembre de ${anio} (${formatEuros(i.deudaViva)} en total).${i.deudaConPrevisto === null ? "" : ` Si se firmara el préstamo previsto, sería de ${formatEuros(i.deudaConPrevistoPorHabitante)} por habitante.`}`,
    },
    {
      titulo: "Deuda sobre los ingresos del año",
      valor: p1(i.deudaSobreIngresosCorrientesPct),
      texto: `Compara lo que se debe con lo que se ingresa en un año. Cuanto menor, más holgura.${i.deudaConPrevisto === null ? "" : ` Si se firmara el préstamo previsto subiría al ${p1(i.deudaConPrevistoSobreIngresosCorrientesPct)}.`}`,
    },
    {
      titulo: "Lo que cuesta la deuda al año",
      valor: formatEuros(i.cargaFinanciera, { compact: true }),
      texto: `Intereses y devolución de préstamos de ${anio} (${p1(i.cargaFinancieraPct)} de los ingresos del año), solo con los préstamos actuales.`,
    },
    {
      titulo: "Dependencia de otras administraciones",
      valor: p1(i.dependenciaTransferenciasPct),
      texto: "Parte de los ingresos del año que llega de otras administraciones (Estado, Junta…) en forma de transferencias, en lugar de impuestos y tasas propios.",
    },
  ];
  main.innerHTML = `
    <h1>Indicadores <span class="muted">${anio}</span></h1>
    <p class="lead">Seis cifras sencillas para entender la situación económica del Ayuntamiento.</p>
    <div class="cards">${tarjetas.map((t) => `<section class="card"><h2 class="card-titulo">${esc(t.titulo)}</h2><p class="cifra">${t.valor}</p><p class="muted">${esc(t.texto)}</p></section>`).join("")}</div>
    <p class="muted">Calculados con las cifras del presupuesto inicial (previsiones), con ${resumen.habitantes.toLocaleString("es-ES")} habitantes (${esc(resumen.fuentePoblacion)}). No son los indicadores oficiales de la liquidación del presupuesto. Más explicaciones en la <a href="guia.html?anio=${anio}">guía</a>.</p>`;
});
