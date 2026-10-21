import { runPage, esc } from "./layout.js";
import { urlDatos } from "./data.js";

const FICHEROS = [
  ["resumen", "Resumen", "Totales, ingresos y gastos por capítulo, reparto por cada 100 € y población."],
  ["ingresos", "Ingresos", "Capítulos y conceptos de ingreso, con el año anterior (y el de hace dos años cuando el Excel lo trae)."],
  ["gastos", "Gastos", "Capítulos, políticas, programas y partidas."],
  ["inversiones", "Inversiones", "Proyectos por programa y cómo se financian."],
  ["subvenciones", "Subvenciones", "Subvenciones nominativas por actividad y por entidad."],
  ["deuda", "Deuda", "Préstamos, deuda viva por año, préstamo previsto y carga financiera."],
];

runPage("descargas", async ({ anio, main }) => {
  main.innerHTML = `
    <h1>Descargas <span class="muted">${anio}</span></h1>
    <p class="lead">Los datos que alimentan esta web, para que puedas usarlos, revisarlos o compararlos.</p>
    <h2>Datos en formato JSON</h2>
    <ul class="descargas">${FICHEROS.map(([f, t, d]) => `<li><a href="${urlDatos(`${anio}/${f}.json`)}" download>${esc(t)} (${f}.json)</a><br><span class="muted">${esc(d)}</span></li>`).join("")}</ul>
    <h2>Licencia de los datos</h2>
    <p>Los datos de esta web (los ficheros JSON y los Excel del presupuesto) se publican con la licencia <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener">Creative Commons Reconocimiento 4.0 (CC BY 4.0)</a>: puedes copiarlos, redistribuirlos y reutilizarlos, también con fines comerciales, siempre que cites la fuente.</p>
    <p><strong>Cómo citar:</strong> «Fuente: Ayuntamiento de Aranda de Duero (presupuestos.arandadeduero.dev), licencia CC BY 4.0».</p>
    <h2>Documentos originales</h2>
    <p>Los Excel del presupuesto del Ayuntamiento, tal como se publicaron, están en el <a href="https://github.com/arandadeduero/visorpresupuesto/tree/main/${anio}" rel="noopener">repositorio del proyecto</a>.</p>
    <p class="muted">Los importes son del presupuesto aprobado. Las cifras «por habitante» usan la población indicada en la página de resumen.</p>`;
});
