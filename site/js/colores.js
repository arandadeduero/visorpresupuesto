// Los colores viven en el CSS (variables de styles.css y escalas.css). Aquí solo se leen, para los sitios donde
// una variable CSS no llega: el lienzo de Chart.js. Nunca se escribe un color en JS ni se toca element.style.

const cache = new Map();
let contexto = null;

/** Convierte cualquier color CSS que entienda el navegador (hex, rgb, color-mix…) en «rgb(r, g, b)» para el canvas. */
export function normalizar(css) {
  if (!contexto) {
    const lienzo = document.createElement("canvas");
    lienzo.width = lienzo.height = 1;
    contexto = lienzo.getContext("2d", { willReadFrequently: true });
  }
  contexto.clearRect(0, 0, 1, 1);
  contexto.fillStyle = "rgb(0, 0, 0)";
  contexto.fillStyle = css; // un valor que no se entiende se ignora y queda el negro de arriba
  contexto.fillRect(0, 0, 1, 1);
  const [r, g, b, a] = contexto.getImageData(0, 0, 1, 1).data;
  return a === 255 ? `rgb(${r}, ${g}, ${b})` : `rgba(${r}, ${g}, ${b}, ${(a / 255).toFixed(3)})`;
}

/** Valor actual de una variable CSS de color (por ejemplo `--cap-1`), ya resuelto, según el tema en vigor. */
export function colorVar(nombre) {
  if (!cache.has(nombre)) {
    const crudo = getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
    cache.set(nombre, crudo ? normalizar(crudo) : "");
  }
  return cache.get(nombre);
}

const consulta = () => (typeof matchMedia === "function" ? matchMedia("(prefers-color-scheme: dark)") : null);

/** ¿Está el sistema en modo oscuro? */
export const esOscuro = () => Boolean(consulta()?.matches);

/** Ejecuta `fn` cada vez que cambia el esquema del sistema (claro/oscuro), con la caché de colores ya vaciada. */
export function alCambiarEsquema(fn) {
  consulta()?.addEventListener("change", () => {
    cache.clear();
    fn();
  });
}
