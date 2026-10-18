// Formato de importes y variaciones, y búsqueda sin tildes. Funciones puras (se prueban con `node --test site/js/`).

const NBSP = " ";
const entero = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 0, useGrouping: false });
// Agrupación de miles a mano: el «es-ES» de Intl no agrupa los números de 4 cifras (3000) y varía entre navegadores.
const agrupar = (n) => entero.format(n).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
const decimal1 = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 1 });

const esNumero = (n) => typeof n === "number" && Number.isFinite(n);

export function formatEuros(n, { compact = false } = {}) {
  if (!esNumero(n)) return "—";
  if (compact && Math.abs(n) >= 1_000_000) return `${decimal1.format(n / 1_000_000)}${NBSP}M€`;
  return `${agrupar(n)}${NBSP}€`;
}

export function formatVariation(actual, anterior) {
  if (!esNumero(actual) && !esNumero(anterior)) return { text: "—", dir: "na" };
  const a = esNumero(actual) ? actual : 0;
  const b = esNumero(anterior) ? anterior : 0;
  if (b === 0) return a > 0 ? { text: "nuevo este año", dir: "new" } : { text: "sin cambios", dir: "flat" };
  const pct = ((a - b) / Math.abs(b)) * 100;
  if (Math.abs(pct) < 0.05) return { text: "sin cambios", dir: "flat" };
  const cifra = Math.abs(pct) < 10 ? decimal1.format(Math.abs(pct)) : agrupar(Math.abs(pct));
  return pct > 0 ? { text: `+${cifra} %`, dir: "up" } : { text: `−${cifra} %`, dir: "down" };
}

export function normalize(texto) {
  return String(texto ?? "")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, (m) => (m === "̃" ? m : ""))
    .normalize("NFC")
    .toLowerCase();
}

// Siglas que usa la gente y que no aparecen en los nombres oficiales.
const SIGLAS = { ibi: "bienes inmuebles", iae: "actividades economicas", ivtm: "traccion mecanica", icio: "instalaciones, construcciones y obras" };

export function matches(texto, consulta) {
  const q = normalize(consulta).trim();
  return normalize(texto).includes(SIGLAS[q] ?? q);
}

export function sumBy(items, fn) {
  return items.reduce((s, x) => s + (esNumero(fn(x)) ? fn(x) : 0), 0);
}
