// Texto que explica por qué el presupuesto muestra dos cifras de préstamo, sin afirmar más de lo que dicen los datos.
import { esc } from "./layout.js";
import { formatEuros } from "./format.js";
import { urlPagina } from "./rutas.js";

export function explicaDosPrestamos(previsto, prestamoInversiones) {
  const diferencia = Math.abs(prestamoInversiones - previsto);
  return (
    `En el presupuesto aparecen dos cifras de préstamo: ${formatEuros(previsto)} en el anexo de deuda y ${formatEuros(prestamoInversiones)} en la financiación de las inversiones y en los ingresos (una diferencia de ${formatEuros(diferencia)}). ` +
    "Los documentos del presupuesto no detallan por qué no coinciden. " +
    "El Ayuntamiento prevé usar remanentes de tesorería (ahorros de años anteriores) para pagar parte de las inversiones en lugar de pedir todo el dinero a los bancos, así que el préstamo realmente necesario puede ser menor que el máximo previsto. " +
    "Son estimaciones y ninguna es una deuda ya contraída."
  );
}

export const fecha = (iso) => iso.split("-").reverse().join("/");
export const mes = (iso) => new Date(`${iso}T12:00:00`).toLocaleDateString("es-ES", { month: "long", year: "numeric" });

// El anexo de deuda de algunos años (2025, 2026) incluye un préstamo previsto; el de otros (2024) no.
export function avisoPrevisto(pv, d, prestamoInversiones, anio) {
  return `<div class="aviso"><h3>Previsión: un préstamo nuevo de ${formatEuros(pv.importe, { compact: true })}</h3>
      <p>El presupuesto prevé un préstamo de <strong>${formatEuros(pv.importe)}</strong> para ${esc(mes(pv.fecha))}, que se empezaría a devolver en ${esc(mes(pv.primeraAmortizacion))} y terminaría en ${esc(mes(pv.ultimaAmortizacion))} (${esc(pv.tipoInteres)}). Si se firmara, la deuda a 31 de diciembre de ${anio} sería de <strong>${formatEuros(d.titular.vivaFinConPrevisto)}</strong>.</p>
      <p><strong>Solo se formalizará si es necesario</strong>, según la liquidación y la ejecución del presupuesto.</p>
      <p>${esc(explicaDosPrestamos(pv.importe, prestamoInversiones))} Por eso el gráfico de abajo no las incluye. Las cifras de préstamo en las <a href="${urlPagina("inversiones", anio)}">inversiones</a> se explican en esa página.</p></div>`;
}

export function avisoSinPrevisto(prestamoInversiones, anio) {
  if (!(prestamoInversiones > 0)) return "";
  return `<div class="aviso"><h3>Préstamos previstos en los ingresos</h3>
      <p>El presupuesto de ${anio} cuenta con <strong>${formatEuros(prestamoInversiones)}</strong> de préstamos para financiar inversiones, pero el anexo de deuda de ese año no recoge ningún préstamo nuevo. Los documentos del presupuesto no detallan si finalmente se pedirían: es una previsión de ingresos, no una deuda contraída. Por eso la deuda y el gráfico de abajo solo incluyen los préstamos que ya existen. Más datos en las <a href="${urlPagina("inversiones", anio)}">inversiones</a>.</p></div>`;
}

/** Aviso de la página de inversiones: el préstamo que financia las obras es una previsión, no una deuda ya contraída. */
export function avisoPrestamoInversiones(prestamo, anio) {
  return `<div class="aviso"><h3>El préstamo es una previsión</h3>
      <p>Los <strong>${formatEuros(prestamo)}</strong> de préstamo son lo máximo previsto en el presupuesto. Solo se pedirían si hacen falta, según la liquidación y la ejecución del presupuesto. El Ayuntamiento puede usar remanentes de tesorería (ahorros de años anteriores) para pagar parte de las obras, así que el préstamo final puede ser menor. Esta cifra es una estimación: depende de lo ya comprometido y de lo que finalmente no se ejecute. <a href="${urlPagina("deuda", anio)}">Ver la página de deuda</a>.</p></div>`;
}
