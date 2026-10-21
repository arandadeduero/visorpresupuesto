// Cabecera, menú, selector de año y pie comunes a todas las páginas.
import { getIndex, getYear, loadData } from "./data.js";
import { activarOrdenacion } from "./ordenar-tablas.js";
import { iniciarAnalitica } from "./analytics.js";
import { URL_POLITICA_PRIVACIDAD } from "./analytics-config.js";
import { fechaLarga } from "./format.js";

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
      ["metodologia", "Metodología", "metodologia.html"],
      ["descargas", "Descargas", "descargas.html"],
    ],
  },
];
export const SECCIONES = GRUPOS.flatMap((g) => g.secciones);

export const esc = (t) =>
  String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

/** La portada se enlaza como «./» y no como «index.html»: así hay una sola URL para ella (la canónica es «/»). */
export const urlPagina = (href) => (href === "index.html" ? "./" : href);

/** Enlaces «Relacionado» de cada página: [página destino, texto del enlace]. Los lee también el build para el HTML estático. */
export const RELACIONADOS = {
  resumen: [["ingresos", "De dónde sale el dinero del Ayuntamiento"], ["gastos", "En qué se gasta, por política de gasto"], ["deuda", "La deuda del Ayuntamiento"], ["indicadores", "Indicadores de endeudamiento y ahorro"]],
  ingresos: [["gastos", "En qué se gasta el dinero del Ayuntamiento"], ["resumen", "Resumen del presupuesto"], ["calculadora", "Calculadora de impuestos: a qué se destina lo que pagas"], ["guia", "Guía de capítulos y conceptos del presupuesto"]],
  gastos: [["ingresos", "De dónde sale el dinero del Ayuntamiento"], ["inversiones", "Inversiones y obras previstas"], ["subvenciones", "Subvenciones a asociaciones y entidades"], ["calculadora", "Calculadora de impuestos: a qué se destina lo que pagas"], ["guia", "Guía de programas y partidas de gasto"]],
  inversiones: [["deuda", "La deuda del Ayuntamiento y los préstamos"], ["gastos", "Gastos por política de gasto"], ["indicadores", "Indicadores de endeudamiento y ahorro"], ["metodologia", "Qué es una previsión y cómo se clasifican los datos"]],
  subvenciones: [["gastos", "Gastos por política de gasto"], ["inversiones", "Inversiones y obras previstas"], ["resumen", "Resumen del presupuesto"], ["descargas", "Descargar los datos de subvenciones"]],
  deuda: [["inversiones", "Inversiones previstas y cómo se pagan"], ["indicadores", "Indicadores de endeudamiento y ahorro"], ["guia", "Guía: deuda viva, amortización e intereses"], ["metodologia", "Cómo se estima el nivel de endeudamiento"]],
  indicadores: [["deuda", "La deuda del Ayuntamiento"], ["ingresos", "De dónde sale el dinero del Ayuntamiento"], ["guia", "Guía: ahorro bruto y nivel de endeudamiento"], ["metodologia", "Metodología y fuentes de los datos"]],
  comparar: [["resumen", "Resumen del presupuesto de un año"], ["gastos", "Gastos por política de gasto"], ["ingresos", "Ingresos por capítulo"], ["descargas", "Descargar los datos de cada año"]],
};

/** Tarjetas de la portada: [página, texto del enlace, explicación]. */
export const TARJETAS_INICIO = [
  ["ingresos", "Ingresos del Ayuntamiento", "De dónde sale el dinero"],
  ["gastos", "Gastos por política", "En qué se gasta, hasta cada partida"],
  ["inversiones", "Inversiones previstas", "Las obras previstas y cómo se pagan"],
  ["subvenciones", "Subvenciones a entidades", "A qué asociaciones se da dinero"],
  ["deuda", "Deuda del Ayuntamiento", "Cuánto se debe y cuándo se paga"],
  ["indicadores", "Indicadores de endeudamiento", "Ahorro, deuda por habitante y más"],
  ["calculadora", "Calculadora de impuestos", "A qué se destina lo que pagas"],
];

export function tarjetasHtml(anio) {
  const consulta = anio === null || anio === undefined ? "" : `?anio=${anio}`;
  const tarjetas = TARJETAS_INICIO
    .map(([id, texto, detalle]) => `<a class="card" href="${urlPagina(SECCIONES.find((s) => s[0] === id)[2])}${consulta}"><strong>${esc(texto)}</strong><span>${esc(detalle)}</span></a>`)
    .join("");
  return `<div class="cards">${tarjetas}</div>`;
}

/** Bloque «Relacionado» con enlaces descriptivos a otras páginas (vacío si la página no tiene). */
export function relacionadoHtml(activa, anio) {
  const lista = RELACIONADOS[activa];
  if (!lista) return "";
  const consulta = anio === null || anio === undefined ? "" : `?anio=${anio}`;
  const items = lista
    .map(([id, texto]) => `<li><a href="${urlPagina(SECCIONES.find((s) => s[0] === id)[2])}${consulta}">${esc(texto)}</a></li>`)
    .join("");
  return `<nav class="relacionado" aria-labelledby="titulo-relacionado"><h2 id="titulo-relacionado">Relacionado</h2><ul>${items}</ul></nav>`;
}

/** HTML del menú: un bloque por grupo, con `aria-current="page"` en la sección activa y `?anio=` en los enlaces. */
export function menuHtml(activa, anio) {
  const consulta = anio === null || anio === undefined ? "" : `?anio=${anio}`;
  return GRUPOS.map((g) => {
    const items = g.secciones
      .map(([id, texto, href]) => `<li><a href="${urlPagina(href)}${consulta}"${id === activa ? ' aria-current="page"' : ""}>${texto}</a></li>`)
      .join("");
    const etiqueta = g.id === "principal" ? "" : `<span class="menu-etiqueta">${g.titulo}</span>`;
    return `<div class="menu-grupo menu-${g.id}">${etiqueta}<ul>${items}</ul></div>`;
  }).join("");
}

/** Ruta del escudo de la cabecera: con build lleva huella y la anota el HTML en data-escudo; sin build, la del fichero. */
export const urlEscudo = () => document.documentElement.dataset.escudo || "img/escudo.png";

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

export const URL_REPOSITORIO = "https://github.com/arandadeduero/visorpresupuesto";

/** Pie común: fuente, enlaces institucionales y fecha de actualización de los datos (ISO, la pone el build). */
export function pieHtml(actualizado, consulta = "") {
  const fecha = actualizado ? `<p class="pie-actualizado">Datos actualizados el ${fechaLarga(actualizado)}.</p>` : "";
  return `<footer class="site"><div class="wrap">
      <p>Fuente: presupuesto inicial del Ayuntamiento de Aranda de Duero. Son previsiones, no gastos ya realizados. Para comparar con otros municipios: <a href="https://presupuestos.gobierto.es/municipios/aranda-de-duero" rel="noopener">Gobierto Presupuestos</a>.</p>
      <p class="pie-enlaces"><a href="https://www.arandadeduero.es" rel="noopener">Ayuntamiento de Aranda de Duero</a> · <a href="https://transparencia.arandadeduero.es" rel="noopener">Portal de transparencia</a> · <a href="${URL_REPOSITORIO}" rel="noopener">Código y datos en GitHub</a> · <a href="${URL_POLITICA_PRIVACIDAD}" rel="noopener">Política de privacidad</a> · <a href="metodologia.html${consulta}">Metodología y fuentes</a></p>
      ${fecha}</div></footer>`;
}

/** Cabecera, menú, contenido y pie. Función pura: la usa el navegador y también el build para el HTML estático. */
export function marcoHtml({ activa, anio, indice, escudo, actualizado, contenido = "", enlazarAnio = true }) {
  const enlaces = enlazarAnio ? anio : null; // el HTML estático enlaza sin «?anio=»: una sola URL por página
  const consulta = enlaces === null ? "" : `?anio=${enlaces}`;
  const opciones = (indice?.anios ?? [])
    .map((a) => `<option value="${a.anio}"${a.anio === anio ? " selected" : ""}>${a.anio} · ${a.tipo === "inicial" ? "presupuesto inicial" : a.tipo}</option>`)
    .join("");
  return `
    <a class="saltar" href="#contenido">Saltar al contenido</a>
    <header class="site">
      <div class="wrap cabecera">
        <a class="marca" href="./${consulta}"><img class="logo" src="${escudo}" alt="Ayuntamiento de Aranda de Duero" width="22" height="33"><span>Presupuestos de Aranda de Duero</span></a>
        <label class="anio">Año <select id="selector-anio" aria-label="Año del presupuesto">${opciones}</select></label>
        <button type="button" id="boton-menu" class="boton-menu" aria-expanded="false" aria-controls="menu-secciones"><span class="hamburguesa" aria-hidden="true"></span><span>Menú</span></button>
      </div>
      <nav class="menu" id="menu-secciones" aria-label="Secciones"><div class="wrap menu-interior">${menuHtml(activa, enlaces)}</div></nav>
    </header>
    <main id="contenido" class="wrap" tabindex="-1">${contenido}</main>
    ${pieHtml(actualizado, consulta)}`;
}

function montarMarco(activa, anio, indice) {
  document.body.innerHTML = marcoHtml({ activa, anio, indice, escudo: urlEscudo(), actualizado: document.documentElement.dataset.actualizado });
  document.getElementById("selector-anio").addEventListener("change", (e) => {
    const url = new URL(location.href);
    url.searchParams.set("anio", e.target.value);
    location.href = url.toString();
  });
  activarMenuMovil();
  iniciarAnalitica(); // aviso de consentimiento y enlace de preferencias; Google no carga hasta que se acepta
  return document.getElementById("contenido");
}

export function showError(main, error) {
  main.innerHTML = `<div class="aviso aviso-error" role="alert"><strong>No podemos mostrar esta página.</strong><p>${esc(error.message)}</p></div>`;
}

/** Pinta el marco y devuelve { anio, main, load }. Si falla, muestra el error en pantalla y devuelve null. */
export async function renderShell(activa) {
  const tituloEstatico = document.title;
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
  // El título estático de cada HTML ya describe la página; aquí solo se le añade el año elegido.
  document.title = `${tituloEstatico} (${anio})`;
  return { anio, main, load: (nombre) => loadData(anio, nombre) };
}

/** Atajo para las páginas: renderShell + captura de errores al dibujar. */
export async function runPage(activa, dibujar) {
  const ctx = await renderShell(activa);
  if (!ctx) return;
  try {
    await dibujar(ctx);
    ctx.main.insertAdjacentHTML("beforeend", relacionadoHtml(activa, ctx.anio));
  } catch (e) {
    showError(ctx.main, e);
  }
}
