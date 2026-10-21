import { runPage, esc } from "./layout.js";
import { formatEuros } from "./format.js";
import { urlPagina } from "./rutas.js";
import { calcularIndicadores, textoNivelEndeudamiento } from "./lecturas.js";

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
      titulo: "Nivel de endeudamiento (estimado)",
      valor: p1(i.deudaSobreIngresosCorrientesPct),
      texto: textoNivelEndeudamiento(i),
    },
    {
      titulo: "Ahorro neto (estimado)",
      valor: formatEuros(i.ahorroNetoEstimado, { compact: true }),
      texto: `Ahorro bruto menos lo que cuesta cada año devolver los préstamos actuales (intereses y amortización): ${p1(i.ahorroNetoEstimadoPct)} de los ingresos del año. Si saliera negativo en la liquidación, la ley no permitiría concertar nuevos préstamos a largo plazo. No incluye el préstamo previsto ni los ajustes de la liquidación.`,
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
    <p class="lead">Siete cifras sencillas para entender la situación económica del Ayuntamiento.</p>
    <div class="cards">${tarjetas.map((t) => `<section class="card"><h2 class="card-titulo">${esc(t.titulo)}</h2><p class="cifra">${t.valor}</p><p class="muted">${esc(t.texto)}</p></section>`).join("")}</div>
    <p class="muted">Calculados con las cifras del presupuesto aprobado (previsiones), con ${resumen.habitantes.toLocaleString("es-ES")} habitantes (${esc(resumen.fuentePoblacion)}). No son los indicadores oficiales de la liquidación del presupuesto. Más explicaciones en la <a href="${urlPagina("guia", anio)}">guía</a>.</p>
    <p class="muted">Normativa del nivel de endeudamiento y del ahorro neto: <a href="https://www.boe.es/buscar/act.php?id=BOE-A-2004-4214#a53" rel="noopener">artículo 53 del texto refundido de la Ley Reguladora de las Haciendas Locales</a> y <a href="https://www.boe.es/buscar/act.php?id=BOE-A-2012-15651" rel="noopener">disposición final 31.ª de la Ley 17/2012</a> (umbral del 75 %). Para las cifras oficiales hay que consultar la liquidación del presupuesto y la Intervención municipal.</p>`;
});
