// Única función que sabe cómo se llega a cada página. Dos modos, según lo que ponga el build en <html>:
//  - Con build (tools/build_site.py): data-raiz="../" (o "" en la raíz) y data-ultimo="2026". Cada año tiene su carpeta
//    (/2025/gastos.html) y las páginas de /2025/ llevan además data-anio="2025". Las de la raíz son el último año.
//  - Sin build (site/ en local): sin data-raiz, el año va en «?anio=» como siempre.
export const PAGINAS_SIN_ANIO = ["comparar", "guia", "metodologia", "descargas"];

const atributos = () => globalThis.document?.documentElement?.dataset ?? {};

/** ¿Es una página construida (con carpetas por año)? */
export const enBuild = () => atributos().raiz !== undefined;

/** Año fijado por la ruta (/2025/…): null en la raíz y en local. */
export const anioDeLaUrl = () => (atributos().anio === undefined ? null : Number(atributos().anio));

/** ¿Es una página de la raíz del sitio (portada, alias del último año, páginas sin año)? */
export const esRaiz = () => enBuild() && anioDeLaUrl() === null;

/** URL relativa de una página. `anio` solo cuenta en las páginas que dependen del año; sin él, el último. */
export function urlPagina(id, anio = null) {
  const fichero = id === "inicio" ? "" : `${id}.html`;
  const d = atributos();
  if (d.raiz === undefined) return (fichero || "./") + (anio === null ? "" : `?anio=${anio}`);
  if (PAGINAS_SIN_ANIO.includes(id)) return d.raiz + fichero;
  const ultimo = Number(d.ultimo);
  const a = anio ?? ultimo;
  if (id === "inicio") return a === ultimo ? d.raiz || "./" : `${d.raiz}${a}/`;
  return `${d.raiz}${a}/${fichero}`;
}

/** Enlaces antiguos («gastos.html?anio=2025») en una página de la raíz: a dónde llevarlos, o null si no hay que moverse. */
export function destinoAntiguo(activa, indice, busqueda, hash = "") {
  if (!esRaiz() || PAGINAS_SIN_ANIO.includes(activa)) return null;
  const params = new URLSearchParams(busqueda);
  const anio = Number(params.get("anio"));
  if (anio === indice.ultimo || !indice.anios.some((a) => a.anio === anio)) return null;
  params.delete("anio");
  const resto = params.toString();
  return urlPagina(activa, anio) + (resto ? `?${resto}` : "") + hash;
}

/** A dónde ir al elegir otro año en el selector: la misma página de ese año (con build) o la misma con ?anio= (sin build). */
export function urlCambioDeAnio(activa, anio, busqueda) {
  if (!enBuild()) {
    const params = new URLSearchParams(busqueda);
    params.set("anio", anio);
    return `?${params}`;
  }
  return urlPagina(PAGINAS_SIN_ANIO.includes(activa) ? "inicio" : activa, anio);
}
