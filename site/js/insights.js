// Lecturas del presupuesto pensadas para el vecino: euros por habitante, qué ha cambiado más y partidas destacadas.
// Funciones puras, sin DOM.

const esNumero = (n) => typeof n === "number" && Number.isFinite(n);

/** Euros por habitante, o null si falta el importe o la población. */
export function porHabitante(importe, habitantes) {
  return esNumero(importe) && esNumero(habitantes) && habitantes > 0 ? importe / habitantes : null;
}

/**
 * Las `n` mayores subidas y bajadas (en euros) entre el año anterior (y2025) y el del presupuesto (y2026).
 * `pct` es null cuando el año anterior era 0 (no se puede calcular un porcentaje).
 */
export function mayoresCambios(items, n = 5) {
  const cambios = items
    .filter((x) => esNumero(x.y2026) || esNumero(x.y2025))
    .map((x) => {
      const anterior = esNumero(x.y2025) ? x.y2025 : 0;
      const actual = esNumero(x.y2026) ? x.y2026 : 0;
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
    importe: item.y2026,
    anterior: item.y2025,
    porHabitante: porHabitante(item.y2026, habitantes),
    pct: total > 0 ? (item.y2026 / total) * 100 : null,
  };
}
