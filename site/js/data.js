// Carga de datos: rutas relativas para que funcione en la subruta /visorpresupuesto/ de GitHub Pages.
import { anioDeLaUrl } from "./rutas.js";

// Única función que conoce dónde están los datos. En local es «data/»; el build (tools/build_site.py) pone
// data-datos="data-<huella>/" en <html> para que cada versión de los datos tenga su propia URL.
export const urlDatos = (ruta) => (globalThis.document?.documentElement?.dataset?.datos ?? "data/") + ruta;

async function leerJson(ruta) {
  let respuesta;
  try {
    respuesta = await fetch(ruta);
  } catch (e) {
    if (location.protocol === "file:") {
      throw new Error("Abre la web desde un servidor, no haciendo doble clic en el fichero (por ejemplo: python3 -m http.server -d site).");
    }
    throw new Error("No se han podido cargar los datos. Comprueba tu conexión e inténtalo de nuevo.");
  }
  if (!respuesta.ok) throw new Error(`No se han encontrado los datos (${ruta}).`);
  return respuesta.json();
}

// Caché por ruta: getIndex lo llaman a la vez el marco, getYear y las páginas, y cada JSON debe bajarse una sola vez.
// Si la petición falla no se guarda, para que el siguiente intento vuelva a pedirlo.
const cache = new Map();
function leerUnaVez(ruta) {
  if (!cache.has(ruta)) {
    cache.set(ruta, leerJson(ruta).catch((e) => {
      cache.delete(ruta);
      throw e;
    }));
  }
  return cache.get(ruta);
}

export const getIndex = () => leerUnaVez(urlDatos("index.json"));

/** Términos del glosario: los comparten la página Guía y el build (que los escribe en el HTML estático). */
export const getGuiaTerminos = () => leerUnaVez(urlDatos("guia-terminos.json"));

export async function getYear() {
  const indice = await getIndex();
  // En /2025/… manda la ruta; en la raíz y en local, «?anio=» y, si no hay, el último año
  const pedido = new URLSearchParams(location.search).get("anio");
  const anio = anioDeLaUrl() ?? (pedido === null ? indice.ultimo : Number(pedido));
  if (!indice.anios.some((a) => a.anio === anio)) throw new Error("Año no disponible: ese presupuesto aún no está publicado. Elige otro año en el selector de arriba.");
  return anio;
}

export const loadData = (anio, nombre) => leerUnaVez(urlDatos(`${anio}/${nombre}.json`));
