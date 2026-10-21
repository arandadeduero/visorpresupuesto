// Google Analytics 4 con consentimiento (RGPD). No se carga ni se envía nada a Google hasta que la persona pulsa
// «Aceptar». La lógica pura (estado del consentimiento, Do Not Track, cookies) se exporta para probarla con node;
// `iniciarAnalitica()` es la única parte que toca el DOM y se llama desde layout.js en todas las páginas.
// Los valores (ID, clave, caducidad, política) están en analytics-config.js.
import { GA_ID, CLAVE_CONSENTIMIENTO, TTL_RECHAZO_MS, URL_POLITICA_PRIVACIDAD } from "./analytics-config.js";

const GRANTED = "granted";
const DENIED = "denied";

/** Decisión vigente a partir del valor guardado: "granted" | "denied" | "" (hay que preguntar).
 *  Aceptar no caduca; rechazar vale TTL_RECHAZO_MS. Valores corruptos o con fecha futura: se pregunta. */
export function estadoConsentimiento(raw, ahoraMs) {
  let guardado;
  try { guardado = JSON.parse(raw); } catch { return ""; }
  if (!guardado || typeof guardado !== "object") return "";
  const { v, t } = guardado;
  if (typeof t !== "number" || !Number.isFinite(t) || t > ahoraMs) return "";
  if (v === GRANTED) return GRANTED;
  if (v === DENIED) return ahoraMs - t < TTL_RECHAZO_MS ? DENIED : "";
  return "";
}

/** Do Not Track activado en el navegador (la propiedad vive en navigator o, en navegadores antiguos, en window). */
export function doNotTrackActivo(nav, win) {
  const v = (x) => x === "1" || x === "yes";
  return v(nav?.doNotTrack) || v(win?.doNotTrack);
}

export const claveDeshabilitar = () => `ga-disable-${GA_ID}`;
export const urlGtag = () => `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(GA_ID)}`;

/** Guarda la decisión. Sin localStorage (privado o bloqueado) no se recuerda: se vuelve a preguntar. */
export function guardarValor(almacen, valor, ahoraMs) {
  try { almacen.setItem(CLAVE_CONSENTIMIENTO, JSON.stringify({ v: valor, t: ahoraMs })); } catch { /* sin almacenamiento */ }
}

/** Nombres de las cookies de Google Analytics (_ga, _ga_XXXX) en una cadena `document.cookie`. */
export function nombresCookiesGa(cookie) {
  return String(cookie || "").split(";").map((c) => c.split("=")[0].trim()).filter((n) => n.startsWith("_ga"));
}

/** Sufijos `; domain=…` para borrar una cookie en el host y en sus dominios superiores (el primero, "", es el host). */
export function dominiosCookie(hostname) {
  const partes = String(hostname || "").split(".");
  const dominios = [""];
  for (let i = 0; i < partes.length - 1; i += 1) dominios.push(`; domain=.${partes.slice(i).join(".")}`);
  return dominios;
}

export const TEXTO_AVISO = "Esta web mide cómo se usa con Google Analytics. No se carga ni se envía nada a Google hasta que pulses “Aceptar”. “Rechazar” no instala nada y se volverá a preguntar pasados 4 días.";

/** HTML del aviso de consentimiento: región accesible, sin estilos en línea (todo con clases). */
export function avisoHtml() {
  return `<section class="aviso-analitica" role="region" aria-label="Aviso sobre analítica web" data-analytics-consent hidden>
    <p class="aviso-analitica-texto">${TEXTO_AVISO} Más información en la <a href="${URL_POLITICA_PRIVACIDAD}" target="_blank" rel="noopener noreferrer">política de privacidad</a>.</p>
    <div class="aviso-analitica-botones">
      <button type="button" class="boton boton-primario" data-analytics-accept>Aceptar</button>
      <button type="button" class="boton" data-analytics-reject>Rechazar</button>
    </div>
  </section>`;
}

/** HTML del enlace del pie que permite cambiar la decisión. */
export const prefsHtml = () => `<p class="pie-privacidad"><button type="button" class="enlace-boton" data-analytics-prefs>Preferencias de analítica</button></p>`;

let gaCargado = false;

/** Carga gtag.js y manda el page_view. Solo se llama con el consentimiento concedido. */
function cargarGa(win, doc) {
  win[claveDeshabilitar()] = false;
  if (gaCargado) return;
  gaCargado = true;
  win.dataLayer = win.dataLayer || [];
  win.gtag = function gtag() { win.dataLayer.push(arguments); }; // gtag.js exige `arguments`, no un array
  win.gtag("js", new Date());
  win.gtag("config", GA_ID);
  const s = doc.createElement("script");
  s.async = true;
  s.src = urlGtag();
  doc.head.appendChild(s);
}

function borrarCookiesGa(win, doc) {
  const dominios = dominiosCookie(win.location?.hostname);
  for (const n of nombresCookiesGa(doc.cookie)) {
    for (const d of dominios) doc.cookie = `${n}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/${d}`;
  }
}

/** Monta el aviso y el enlace de preferencias y aplica la decisión guardada. Debe llamarse con el marco ya pintado. */
export function iniciarAnalitica(win = window, doc = document) {
  if (doNotTrackActivo(win.navigator, win)) return; // Do Not Track: ni aviso, ni Google, ni enlace de preferencias
  const pie = doc.querySelector("footer.site .wrap");
  if (pie && !pie.querySelector("[data-analytics-prefs]")) pie.insertAdjacentHTML("beforeend", prefsHtml());
  if (!doc.querySelector("[data-analytics-consent]")) doc.body.insertAdjacentHTML("beforeend", avisoHtml());
  const aviso = doc.querySelector("[data-analytics-consent]");
  const mostrar = (si) => { aviso.hidden = !si; doc.body.classList.toggle("con-aviso-analitica", si); };

  let almacen = null;
  try { almacen = win.localStorage; } catch { /* sin almacenamiento */ }
  let estado = "";
  try { estado = estadoConsentimiento(almacen?.getItem(CLAVE_CONSENTIMIENTO), Date.now()); } catch { /* se pregunta */ }
  if (estado === GRANTED) cargarGa(win, doc);
  mostrar(estado === "");

  aviso.querySelector("[data-analytics-accept]").addEventListener("click", () => {
    if (almacen) guardarValor(almacen, GRANTED, Date.now());
    cargarGa(win, doc);
    mostrar(false);
  });
  aviso.querySelector("[data-analytics-reject]").addEventListener("click", () => {
    if (almacen) guardarValor(almacen, DENIED, Date.now());
    win[claveDeshabilitar()] = true;
    mostrar(false);
  });
  doc.querySelector("[data-analytics-prefs]")?.addEventListener("click", () => {
    // retirar el consentimiento: borra la decisión, detiene el seguimiento, borra las cookies y vuelve a preguntar
    try { almacen?.removeItem(CLAVE_CONSENTIMIENTO); } catch { /* sin almacenamiento */ }
    win[claveDeshabilitar()] = true;
    borrarCookiesGa(win, doc);
    mostrar(true);
    aviso.querySelector("[data-analytics-accept]").focus();
  });
}
