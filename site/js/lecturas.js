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
  const total = politicas.reduce((s, p) => s + p.y2026, 0);
  if (total <= 0) return [];
  return politicas
    .filter((p) => p.y2026 > 0)
    .map((p) => ({ codigo: p.codigo, nombre: p.nombre, importe: (importe * p.y2026) / total }))
    .sort((a, b) => b.importe - a.importe);
}

const sumaCaps = (capitulos, caps) => capitulos.filter((c) => caps.includes(c.cap)).reduce((s, c) => s + (c.y2026 ?? 0), 0);
const pct = (parte, todo) => (todo > 0 ? (parte / todo) * 100 : null);

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
    deudaConPrevisto,
    deudaPorHabitante: porHabitante(deudaViva, hab),
    deudaConPrevistoPorHabitante: porHabitante(deudaConPrevisto, hab),
    deudaSobreIngresosCorrientesPct: pct(deudaViva, ingresosCorrientes),
    deudaConPrevistoSobreIngresosCorrientesPct: pct(deudaConPrevisto, ingresosCorrientes),
    cargaFinanciera: deuda.carga.total,
    cargaFinancieraPct: pct(deuda.carga.total, ingresosCorrientes),
  };
}
