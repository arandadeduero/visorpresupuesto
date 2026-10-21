// Anchos y proporciones sin estilos en línea: devuelven el nombre de una clase de css/escalas.css
// (.ancho-0 … .ancho-100 y .crece-1 … .crece-100, generadas por tools/generar_escalas.py).

const porcentaje = (valor, total) => (total > 0 && valor > 0 ? Math.min(100, Math.max(1, Math.round((valor / total) * 100))) : 0);

/** Clase de ancho para `valor` sobre `max` (0 si no hay nada; cualquier valor > 0 se ve, como mínimo 1 %). */
export const claseAncho = (valor, max) => `ancho-${porcentaje(valor, max)}`;

/** Clase de flex-grow proporcional de `valor` sobre `total` (como mínimo 1, para que ningún trozo desaparezca). */
export const claseCrece = (valor, total) => `crece-${Math.max(1, porcentaje(valor, total))}`;
