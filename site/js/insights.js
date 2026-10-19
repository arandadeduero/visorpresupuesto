// Lecturas del presupuesto pensadas para el vecino: euros por habitante, qué ha cambiado más y partidas destacadas.
// Funciones puras, sin DOM.

const esNumero = (n) => typeof n === "number" && Number.isFinite(n);

/** Euros por habitante, o null si falta el importe o la población. */
export function porHabitante(importe, habitantes) {
  return esNumero(importe) && esNumero(habitantes) && habitantes > 0 ? importe / habitantes : null;
}

/**
 * Las `n` mayores subidas y bajadas (en euros) entre el año anterior y el del presupuesto.
 * `pct` es null cuando el año anterior era 0 (no se puede calcular un porcentaje).
 */
export function mayoresCambios(items, n = 5) {
  const cambios = items
    .filter((x) => esNumero(x.actual) || esNumero(x.anterior))
    .map((x) => {
      const anterior = esNumero(x.anterior) ? x.anterior : 0;
      const actual = esNumero(x.actual) ? x.actual : 0;
      return { ...x, anterior, actual, delta: actual - anterior, pct: anterior === 0 ? null : ((actual - anterior) / Math.abs(anterior)) * 100 };
    })
    .filter((x) => Math.abs(x.delta) > 0.005);
  return {
    suben: cambios.filter((x) => x.delta > 0).sort((a, b) => b.delta - a.delta).slice(0, n),
    bajan: cambios.filter((x) => x.delta < 0).sort((a, b) => a.delta - b.delta).slice(0, n),
  };
}

/** Ficha de una política (o programa) para «¿Cuánto se gasta en…?». */
export function destacar(item, total, habitantes) {
  return {
    nombre: item.nombre,
    importe: item.actual,
    anterior: item.anterior,
    porHabitante: porHabitante(item.actual, habitantes),
    pct: total > 0 ? (item.actual / total) * 100 : null,
  };
}
