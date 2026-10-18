// Cabecera, menú, selector de año y pie comunes a todas las páginas.
import { getIndex, getYear, loadData } from "./data.js";

const SECCIONES = [
  ["inicio", "Inicio", "index.html"],
  ["resumen", "Resumen", "resumen.html"],
  ["ingresos", "Ingresos", "ingresos.html"],
  ["gastos", "Gastos", "gastos.html"],
  ["inversiones", "Inversiones", "inversiones.html"],
  ["subvenciones", "Subvenciones", "subvenciones.html"],
  ["deuda", "Deuda", "deuda.html"],
];

export const esc = (t) =>
  String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

function montarMarco(activa, anio, indice) {
  const consulta = anio === null ? "" : `?anio=${anio}`;
  const enlaces = SECCIONES.map(
    ([id, texto, href]) => `<a href="${href}${consulta}"${id === activa ? ' aria-current="page"' : ""}>${texto}</a>`,
  ).join("");
  const opciones = (indice?.anios ?? [])
    .map((a) => `<option value="${a.anio}"${a.anio === anio ? " selected" : ""}>${a.anio} · ${a.tipo === "inicial" ? "presupuesto inicial" : a.tipo}</option>`)
    .join("");
  document.body.innerHTML = `
    <a class="saltar" href="#contenido">Saltar al contenido</a>
    <header class="site">
      <div class="wrap cabecera">
        <a class="marca" href="index.html${consulta}">Presupuestos de Aranda de Duero</a>
        <label class="anio">Año <select id="selector-anio" aria-label="Año del presupuesto">${opciones}</select></label>
      </div>
      <nav class="wrap menu" aria-label="Secciones">${enlaces}</nav>
    </header>
    <main id="contenido" class="wrap" tabindex="-1"></main>
    <footer class="site"><div class="wrap">Fuente: presupuesto inicial del Ayuntamiento de Aranda de Duero. Son previsiones, no gastos ya realizados.</div></footer>`;
  document.getElementById("selector-anio").addEventListener("change", (e) => {
    const url = new URL(location.href);
    url.searchParams.set("anio", e.target.value);
    location.href = url.toString();
  });
  return document.getElementById("contenido");
}

export function showError(main, error) {
  main.innerHTML = `<div class="aviso aviso-error" role="alert"><strong>No podemos mostrar esta página.</strong><p>${esc(error.message)}</p></div>`;
}

/** Pinta el marco y devuelve { anio, main, load }. Si falla, muestra el error en pantalla y devuelve null. */
export async function renderShell(activa) {
  let indice = null;
  let anio = null;
  let fallo = null;
  try {
    indice = await getIndex();
    anio = await getYear();
  } catch (e) {
    fallo = e;
  }
  const main = montarMarco(activa, anio, indice);
  if (fallo) {
    showError(main, fallo);
    return null;
  }
  document.title = `${SECCIONES.find((s) => s[0] === activa)[1]} ${anio} · Presupuestos de Aranda de Duero`;
  return { anio, main, load: (nombre) => loadData(anio, nombre) };
}

/** Atajo para las páginas: renderShell + captura de errores al dibujar. */
export async function runPage(activa, dibujar) {
  const ctx = await renderShell(activa);
  if (!ctx) return;
  try {
    await dibujar(ctx);
  } catch (e) {
    showError(ctx.main, e);
  }
}
