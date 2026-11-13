// Piezas de interfaz compartidas por varias páginas.
import { esc } from "./layout.js";
import { formatEuros, formatPct, formatVariation } from "./format.js";
import { porHabitante } from "./insights.js";
import { claseAncho } from "./escalas.js";

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
  const tag = clicable ? "button" : "div";
  const attrs = clicable ? ` type="button" data-id="${esc(id)}" aria-expanded="false"` : "";
  const t = title ? ` title="${esc(title)}"` : "";
  return `<${tag} class="fila"${attrs}${t}>
    <span class="nombre">${clicable ? "▸ " : ""}${esc(nombre)}</span><span class="importe">${formatEuros(importe)}</span>
    <span class="pista" aria-hidden="true"><span class="relleno ${claseAncho(importe, max)}"></span></span>
    ${extra ? `<span class="extra">${extra}</span>` : ""}
  </${tag}>`;
}

export const tablaHtml = (cabeceras, filas) => `<div class="tabla-scroll"><table class="datos">
  <thead><tr>${cabeceras.map((c) => `<th${c.num ? ' class="num"' : ""}>${esc(c.texto)}</th>`).join("")}</tr></thead>
  <tbody>${filas.join("")}</tbody></table></div>`;

/** «12,3 % del total». */
export const delTotal = (importe, total) => `${formatPct((importe / total) * 100)} del total`;

/** Hace desplegables las filas clicables de `contenedor`: al abrir una por primera vez pinta dentro `hijosHtml(id de la fila)`. */
export function activarDesplegables(contenedor, hijosHtml) {
  contenedor.addEventListener("click", (e) => {
    const boton = e.target.closest("button.fila");
    if (!boton) return;
    const hijos = boton.nextElementSibling;
    const abrir = hijos.hidden;
    if (abrir && !hijos.innerHTML) hijos.innerHTML = hijosHtml(boton.dataset.id);
    hijos.hidden = !abrir;
    boton.setAttribute("aria-expanded", String(abrir));
    const nombre = boton.querySelector(".nombre").firstChild;
    nombre.textContent = (abrir ? "▾ " : "▸ ") + nombre.textContent.slice(2);
  });
}

/** «117 € por habitante» (cadena vacía si no hay población). */
export function porHabHtml(importe, habitantes) {
  const v = porHabitante(importe, habitantes);
  return v === null ? "" : `${formatEuros(v)} por habitante`;
}
