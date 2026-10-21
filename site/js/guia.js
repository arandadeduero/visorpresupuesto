import { runPage, esc } from "./layout.js";
import { getGuiaTerminos } from "./data.js";
import { idTermino } from "./format.js";
import { urlPagina } from "./rutas.js";

runPage("guia", async ({ anio, main }) => {
  const terminos = await getGuiaTerminos();
  main.innerHTML = `
    <h1>Guía: las palabras del presupuesto</h1>
    <p class="lead">Qué significan los términos que verás en esta web.</p>
    <dl class="glosario">${terminos.map(({ termino: t, definicion: d, enlace }) => `<dt id="${esc(idTermino(t))}">${esc(t)}</dt><dd>${esc(d)}${enlace ? ` <a href="${esc(enlace.url)}" rel="noopener">${esc(enlace.texto)}</a>.` : ""}</dd>`).join("")}</dl>
    <p class="muted">¿Echas en falta alguna palabra? <a href="https://github.com/arandadeduero/visorpresupuesto/issues" rel="noopener">Cuéntanoslo</a>. Para ver los datos de ${anio}, vuelve al <a href="${urlPagina("inicio", anio)}">inicio</a>.</p>`;
});
