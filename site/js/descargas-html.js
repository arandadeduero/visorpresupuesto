// Página de Descargas: un bloque por presupuesto publicado (no depende del año elegido). Función pura, se prueba en Node.
import { esc, nombreTipo, URL_REPOSITORIO } from "./layout.js";
import { urlDatos } from "./data.js";

const FICHEROS = [
  ["resumen", "Resumen", "Totales, ingresos y gastos por capítulo, reparto por cada 100 € y población."],
  ["ingresos", "Ingresos", "Capítulos y conceptos de ingreso, con el año anterior cuando el presupuesto lo trae."],
  ["gastos", "Gastos", "Capítulos, políticas, programas y partidas."],
  ["inversiones", "Inversiones", "Proyectos por programa y cómo se financian."],
  ["subvenciones", "Subvenciones", "Subvenciones nominativas por actividad y por entidad."],
  ["deuda", "Deuda", "Préstamos, deuda viva por año, préstamo previsto y carga financiera."],
];

const urlDocumento = (anio, nombre) => `${URL_REPOSITORIO}/raw/main/${anio}/${encodeURIComponent(nombre)}`;
const lista = (items) => `<ul class="descargas">${items.join("")}</ul>`;

function bloque({ anio, tipo, origen, documentos = [] }) {
  const json = FICHEROS.map(([f, t, d]) => `<li><a href="${urlDatos(`${anio}/${f}.json`)}" download>${esc(t)} ${anio} (${f}.json)</a><br><span class="muted">${esc(d)}</span></li>`);
  const enlaces = (ext) => documentos.filter((n) => n.endsWith(ext)).map((n) => `<li><a href="${urlDocumento(anio, n)}" rel="noopener">${esc(n)}</a></li>`);
  const pdfs = enlaces(".pdf");
  const excels = enlaces(".xlsx");
  return `<h2 id="presupuesto-${anio}">Presupuesto ${anio} <span class="muted">· ${esc(nombreTipo(tipo))}</span></h2>
    <h3>Datos en formato JSON</h3>${lista(json)}
    ${pdfs.length ? `<h3>Presupuesto completo del Ayuntamiento (PDF)</h3>${lista(pdfs)}` : ""}
    ${excels.length ? `<h3>${origen === "pdf" ? "Excel preparados a partir del PDF" : "Excel originales del Ayuntamiento"}</h3>${lista(excels)}` : ""}
    ${origen === "pdf" ? `<p class="muted">De ${anio} el Ayuntamiento solo publicó el PDF: estos Excel se han preparado copiando sus tablas.</p>` : ""}`;
}

export function descargasHtml(indice) {
  const anios = [...indice.anios].sort((a, b) => b.anio - a.anio);
  return `
    <h1>Descargas</h1>
    <p class="lead">Los datos que alimentan esta web, para que puedas usarlos, revisarlos o compararlos: los ficheros JSON de cada presupuesto, el PDF completo y los Excel del Ayuntamiento.</p>
    <p>Ir a: ${anios.map((a) => `<a href="#presupuesto-${a.anio}">${a.anio}</a>`).join(" · ")}</p>
    <h2>Licencia de los datos</h2>
    <p>Los datos de esta web (los ficheros JSON y los Excel del presupuesto) se publican con la licencia <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener">Creative Commons Reconocimiento 4.0 (CC BY 4.0)</a>: puedes copiarlos, redistribuirlos y reutilizarlos, también con fines comerciales, siempre que cites la fuente.</p>
    <p><strong>Cómo citar:</strong> «Fuente: Ayuntamiento de Aranda de Duero (presupuestos.arandadeduero.es), licencia CC BY 4.0».</p>
    ${anios.map(bloque).join("")}
    <p>Todos los documentos están también en el <a href="${URL_REPOSITORIO}" rel="noopener">repositorio del proyecto</a>, en una carpeta por año.</p>
    <p class="muted">Los importes son previsiones del presupuesto de cada año, no gastos ya realizados. Las cifras «por habitante» usan la población indicada en la página de resumen de cada año.</p>`;
}
