// Texto que explica por qué el presupuesto muestra dos cifras de préstamo, sin afirmar más de lo que dicen los datos.
import { formatEuros } from "./format.js";

export function explicaDosPrestamos(previsto, prestamoInversiones) {
  const diferencia = Math.abs(prestamoInversiones - previsto);
  return (
    `En el presupuesto aparecen dos cifras de préstamo: ${formatEuros(previsto)} en el anexo de deuda y ${formatEuros(prestamoInversiones)} en la financiación de las inversiones y en los ingresos (una diferencia de ${formatEuros(diferencia)}). ` +
    "Los documentos del presupuesto no detallan por qué no coinciden. " +
    "El Ayuntamiento prevé usar remanentes de tesorería (ahorros de años anteriores) para pagar parte de las inversiones en lugar de pedir todo el dinero a los bancos, así que el préstamo realmente necesario puede ser menor que el máximo previsto. " +
    "Son estimaciones y ninguna es una deuda ya contraída."
  );
}
