// Piezas de interfaz compartidas por varias páginas.
import { esc } from "./layout.js";
import { formatEuros, formatVariation } from "./format.js";

/** «▲ +5 % frente al año anterior», «nuevo este año»… con el color y la flecha adecuados (nunca solo color). */
export function variacionHtml(actual, anterior, etiqueta = "frente al año anterior") {
  const v = formatVariation(actual, anterior);
  if (v.dir === "na") return "";
  const flecha = { up: "▲", down: "▼", flat: "＝", new: "●" }[v.dir];
  const clase = v.dir === "up" ? "var-up" : v.dir === "down" ? "var-down" : "";
  const sufijo = v.dir === "up" || v.dir === "down" ? ` ${etiqueta}` : "";
  return `<span class="${clase}">${flecha} ${esc(v.text)}${sufijo}</span>`;
}

/** Fila con barra proporcional a `max`. Si `clicable`, es un botón que despliega. */
export function filaHtml({ id, nombre, title, importe, max, extra = "", clicable = false }) {
  const ancho = max > 0 ? Math.max(0, Math.min(100, (importe / max) * 100)) : 0;
  const tag = clicable ? "button" : "div";
  const attrs = clicable ? ` type="button" data-id="${esc(id)}" aria-expanded="false"` : "";
  const t = title ? ` title="${esc(title)}"` : "";
  return `<${tag} class="fila"${attrs}${t}>
    <span class="nombre">${clicable ? "▸ " : ""}${esc(nombre)}</span><span class="importe">${formatEuros(importe)}</span>
    <span class="pista" aria-hidden="true"><span class="relleno" style="width:${ancho.toFixed(1)}%"></span></span>
    ${extra ? `<span class="extra">${extra}</span>` : ""}
  </${tag}>`;
}

export const tablaHtml = (cabeceras, filas) => `<div class="tabla-scroll"><table class="datos">
  <thead><tr>${cabeceras.map((c) => `<th${c.num ? ' class="num"' : ""}>${esc(c.texto)}</th>`).join("")}</tr></thead>
  <tbody>${filas.join("")}</tbody></table></div>`;
