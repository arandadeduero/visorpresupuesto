// Carga de datos: rutas relativas para que funcione en la subruta /visorpresupuesto/ de GitHub Pages.

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

export const getIndex = () => leerJson("data/index.json");

export async function getYear() {
  const indice = await getIndex();
  const pedido = new URLSearchParams(location.search).get("anio");
  const anio = pedido === null ? indice.ultimo : Number(pedido);
  if (!indice.anios.some((a) => a.anio === anio)) throw new Error("Año no disponible");
  return anio;
}

export const loadData = (anio, nombre) => leerJson(`data/${anio}/${nombre}.json`);
