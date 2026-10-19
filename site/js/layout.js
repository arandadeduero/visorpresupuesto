// Cabecera, menú, selector de año y pie comunes a todas las páginas.
import { getIndex, getYear, loadData } from "./data.js";
import { activarOrdenacion } from "./ordenar-tablas.js";

// Menú en dos niveles: lo principal (grande) y las herramientas (pequeño). Único sitio donde se declaran las páginas.
export const GRUPOS = [
  {
    id: "principal",
    titulo: "Secciones",
    secciones: [
      ["inicio", "Inicio", "index.html"],
      ["resumen", "Resumen", "resumen.html"],
      ["ingresos", "Ingresos", "ingresos.html"],
      ["gastos", "Gastos", "gastos.html"],
      ["inversiones", "Inversiones", "inversiones.html"],
      ["subvenciones", "Subvenciones", "subvenciones.html"],
      ["deuda", "Deuda", "deuda.html"],
    ],
  },
  {
    id: "herramientas",
    titulo: "Herramientas",
    secciones: [
      ["comparar", "Comparar", "comparar.html"],
      ["indicadores", "Indicadores", "indicadores.html"],
      ["calculadora", "Calculadora", "calculadora.html"],
      ["guia", "Guía", "guia.html"],
      ["descargas", "Descargas", "descargas.html"],
    ],
  },
];
export const SECCIONES = GRUPOS.flatMap((g) => g.secciones);

export const esc = (t) =>
  String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

/** HTML del menú: un bloque por grupo, con `aria-current="page"` en la sección activa y `?anio=` en los enlaces. */
export function menuHtml(activa, anio) {
  const consulta = anio === null || anio === undefined ? "" : `?anio=${anio}`;
  return GRUPOS.map((g) => {
    const items = g.secciones
      .map(([id, texto, href]) => `<li><a href="${href}${consulta}"${id === activa ? ' aria-current="page"' : ""}>${texto}</a></li>`)
      .join("");
    const etiqueta = g.id === "principal" ? "" : `<span class="menu-etiqueta">${g.titulo}</span>`;
    return `<div class="menu-grupo menu-${g.id}">${etiqueta}<ul>${items}</ul></div>`;
  }).join("");
}

function activarMenuMovil() {
  const cab = document.querySelector("header.site");
  const boton = document.getElementById("boton-menu");
  const menu = document.getElementById("menu-secciones");
  if (!cab || !boton || !menu) return;
  const abrir = (si, devolverFoco = false) => {
    if (si) cab.setAttribute("data-abierto", "");
    else cab.removeAttribute("data-abierto");
    boton.setAttribute("aria-expanded", String(si));
    if (!si && devolverFoco) boton.focus();
  };
  boton.addEventListener("click", () => abrir(!cab.hasAttribute("data-abierto")));
  menu.addEventListener("click", (e) => { if (e.target.closest("a")) abrir(false); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && cab.hasAttribute("data-abierto")) abrir(false, true);
  });
  document.addEventListener("click", (e) => {
    if (cab.hasAttribute("data-abierto") && !cab.contains(e.target)) abrir(false);
  });
}

function montarMarco(activa, anio, indice) {
  const consulta = anio === null ? "" : `?anio=${anio}`;
  const opciones = (indice?.anios ?? [])
    .map((a) => `<option value="${a.anio}"${a.anio === anio ? " selected" : ""}>${a.anio} · ${a.tipo === "inicial" ? "presupuesto inicial" : a.tipo}</option>`)
    .join("");
  document.body.innerHTML = `
    <a class="saltar" href="#contenido">Saltar al contenido</a>
    <header class="site">
      <div class="wrap cabecera">
        <a class="marca" href="index.html${consulta}">Presupuestos de Aranda de Duero</a>
        <label class="anio">Año <select id="selector-anio" aria-label="Año del presupuesto">${opciones}</select></label>
        <button type="button" id="boton-menu" class="boton-menu" aria-expanded="false" aria-controls="menu-secciones"><span class="hamburguesa" aria-hidden="true"></span><span>Menú</span></button>
      </div>
      <nav class="menu" id="menu-secciones" aria-label="Secciones"><div class="wrap menu-interior">${menuHtml(activa, anio)}</div></nav>
    </header>
    <main id="contenido" class="wrap" tabindex="-1"></main>
    <footer class="site"><div class="wrap">Fuente: presupuesto inicial del Ayuntamiento de Aranda de Duero. Son previsiones, no gastos ya realizados. Para comparar con otros municipios: <a href="https://presupuestos.gobierto.es/municipios/aranda-de-duero" rel="noopener">Gobierto Presupuestos</a>.</div></footer>`;
  document.getElementById("selector-anio").addEventListener("change", (e) => {
    const url = new URL(location.href);
    url.searchParams.set("anio", e.target.value);
    location.href = url.toString();
  });
  activarMenuMovil();
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
  activarOrdenacion(main);
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
