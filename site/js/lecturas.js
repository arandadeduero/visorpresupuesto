// Cálculos de las páginas «Calculadora» e «Indicadores». Funciones puras, sin DOM.
import { porHabitante } from "./insights.js";

/** Convierte lo que escribe el vecino («1.234,56», «350 €») en un importe ≥ 0; 0 si no se entiende. */
export function parseImporte(texto) {
  if (texto === null || texto === undefined) return 0;
  const limpio = String(texto).replace(/[€\s]/g, "").replace(/\.(?=\d{3}(\D|$))/g, "").replace(",", ".");
  const n = Number(limpio);
  return Number.isFinite(n) && n > 0 ? n : 0;
}

/** Reparte `importe` entre las políticas de gasto en proporción a su gasto previsto (orientativo). */
export function repartoAportacion(importe, politicas) {
  if (!Number.isFinite(importe) || importe <= 0) return [];
  const total = politicas.reduce((s, p) => s + p.actual, 0);
  if (total <= 0) return [];
  return politicas
    .filter((p) => p.actual > 0)
    .map((p) => ({ codigo: p.codigo, nombre: p.nombre, importe: (importe * p.actual) / total }))
    .sort((a, b) => b.importe - a.importe);
}

const sumaCaps = (capitulos, caps) => capitulos.filter((c) => caps.includes(c.cap)).reduce((s, c) => s + (c.actual ?? 0), 0);
const pct = (parte, todo) => (Number.isFinite(parte) && todo > 0 ? (parte / todo) * 100 : null);

// Umbrales legales del nivel de endeudamiento de las entidades locales (capital vivo / ingresos corrientes):
// - 75 %: por debajo (y con ahorro neto positivo) se pueden concertar préstamos a largo plazo para inversiones sin
//   autorización previa (disposición adicional 14.ª del RDL 20/2011, redactada por la DF 31.ª de la Ley 17/2012).
// - 110 %: por encima no se pueden concertar préstamos a largo plazo (misma disposición y art. 53.2 del TRLRHL, RDL 2/2004).
export const UMBRAL_AUTORIZACION_PCT = 75;
export const UMBRAL_PROHIBICION_PCT = 110;

/** «bajo75» (no pasa del 75 %), «entre75y110» (pasa del 75 % sin pasar del 110 %), «sobre110», o null si no hay dato. */
export function situacionEndeudamiento(pctNivel) {
  if (!Number.isFinite(pctNivel)) return null;
  if (pctNivel <= UMBRAL_AUTORIZACION_PCT) return "bajo75";
  return pctNivel <= UMBRAL_PROHIBICION_PCT ? "entre75y110" : "sobre110";
}

const pct1 = (n) => `${n.toLocaleString("es-ES", { maximumFractionDigits: 1 })} %`;

/** Texto llano de la tarjeta «Nivel de endeudamiento»: qué mide, qué dice la ley y dónde queda el Ayuntamiento. */
export function textoNivelEndeudamiento(i) {
  const hayPrevisto = Number.isFinite(i.deudaConPrevistoSobreIngresosCorrientesPct);
  const peor = hayPrevisto ? i.deudaConPrevistoSobreIngresosCorrientesPct : i.deudaSobreIngresosCorrientesPct;
  const situacion = situacionEndeudamiento(peor);
  const partes = [
    "Compara la deuda viva (los préstamos pendientes de devolver) con los ingresos corrientes del año (capítulos 1 a 5 de ingresos: impuestos, tasas, transferencias corrientes e ingresos patrimoniales).",
    "Según la ley de haciendas locales, con ahorro neto positivo y por debajo del 75 % se pueden pedir préstamos a largo plazo para inversiones sin autorización previa; entre el 75 % y el 110 % hace falta la autorización de la administración que tutela las finanzas locales, y por encima del 110 % no se pueden concertar.",
  ];
  if (hayPrevisto) partes.push(`Si se firmara el préstamo previsto subiría al ${pct1(i.deudaConPrevistoSobreIngresosCorrientesPct)}.`);
  if (situacion === "bajo75") partes.push(`${hayPrevisto ? "Incluso así" : "Con esta cifra"} quedaría por debajo del 75 %.`);
  else if (situacion === "entre75y110") partes.push("Con esta cifra superaría el 75 % y necesitaría autorización para endeudarse a largo plazo.");
  else if (situacion === "sobre110") partes.push("Con esta cifra superaría el 110 % y no podría concertar nuevos préstamos a largo plazo.");
  partes.push("Es una estimación con el presupuesto inicial: la ley usa los ingresos liquidados del año anterior y descuenta los ingresos extraordinarios o afectados.");
  return partes.join(" ");
}

/** Indicadores sencillos de la situación económica, calculados con las cifras del propio presupuesto. */
export function calcularIndicadores({ resumen, ingresos, deuda }) {
  const hab = resumen.habitantes;
  const ingresosCorrientes = sumaCaps(ingresos.capitulos, [1, 2, 3, 4, 5]);
  const gastosCorrientes = sumaCaps(resumen.gastosPorCapitulo, [1, 2, 4]); // sin intereses (capítulo 3)
  const impuestos = sumaCaps(ingresos.capitulos, [1, 2]);
  const tasas = sumaCaps(ingresos.capitulos, [3]);
  const transferencias = sumaCaps(ingresos.capitulos, [4]);
  const ahorroBruto = ingresosCorrientes - gastosCorrientes;
  const deudaViva = deuda.titular.vivaFin;
  const deudaConPrevisto = deuda.titular.vivaFinConPrevisto;
  return {
    ingresosCorrientes,
    gastosCorrientes,
    ahorroBruto,
    ahorroBrutoPct: pct(ahorroBruto, ingresosCorrientes),
    impuestosPorHabitante: porHabitante(impuestos, hab),
    impuestosYTasasPorHabitante: porHabitante(impuestos + tasas, hab),
    dependenciaTransferenciasPct: pct(transferencias, ingresosCorrientes),
    deudaViva,
    deudaConPrevisto, // null si el anexo de deuda de ese año no trae un préstamo previsto
    deudaPorHabitante: porHabitante(deudaViva, hab),
    deudaConPrevistoPorHabitante: porHabitante(deudaConPrevisto, hab),
    deudaSobreIngresosCorrientesPct: pct(deudaViva, ingresosCorrientes),
    deudaConPrevistoSobreIngresosCorrientesPct: pct(deudaConPrevisto, ingresosCorrientes),
    // Aproximación al «ahorro neto» del art. 53.1 TRLRHL: ahorro bruto menos la anualidad de los préstamos actuales
    // (intereses + amortización del año). No incluye el préstamo previsto ni los ajustes de la liquidación.
    ahorroNetoEstimado: ahorroBruto - deuda.carga.total,
    ahorroNetoEstimadoPct: pct(ahorroBruto - deuda.carga.total, ingresosCorrientes),
    cargaFinanciera: deuda.carga.total,
    cargaFinancieraPct: pct(deuda.carga.total, ingresosCorrientes),
  };
}
