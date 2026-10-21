// Saca de los módulos JS de la web lo que el build necesita para el HTML estático, para no repetirlo en Python:
// el marco (cabecera, menú, pie), el bloque «Relacionado», «Otros años», las tarjetas de la portada, las URLs de las páginas,
// los avisos y los indicadores. Lo calcula para cada «entorno»: cada año publicado (páginas de /<año>/, que van un nivel por
// debajo de la raíz) y «raiz» (portada, alias del último año y páginas sin año), con los mismos atributos data-* que el build
// pone en <html>, que es lo que lee rutas.js.
// Uso: node tools/exportar_js.mjs <carpeta site> <ruta del escudo con huella> <fecha ISO de los datos> > salida.json
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const site = resolve(process.argv[2] ?? "site");
const escudo = process.argv[3] ?? "img/escudo.png";
const actualizado = process.argv[4];
const importar = (ruta) => import(pathToFileURL(join(site, "js", ruta)).href);
const leer = (ruta) => JSON.parse(readFileSync(join(site, "data", ruta), "utf8"));

// layout.js importa módulos que tocan el DOM solo al ejecutarse en el navegador; aquí solo se usan sus funciones puras.
const layout = await importar("layout.js");
const rutas = await importar("rutas.js");
const lecturas = await importar("lecturas.js");
const textos = await importar("deuda-texto.js");
const indice = leer("index.json");
const ultimo = indice.ultimo;
const MARCA = "<!--CONTENIDO-->";

/** Ejecuta `fn` como si <html> llevara estos data-* (rutas.js los lee de document). */
function conAtributos(dataset, fn) {
  globalThis.document = { documentElement: { dataset } };
  try {
    return fn();
  } finally {
    delete globalThis.document;
  }
}

function entorno(anio, dataset, escudoRelativo) {
  return conAtributos(dataset, () => {
    const marcos = {};
    const relacionados = {};
    const anios = {};
    const urls = {};
    for (const [id] of layout.SECCIONES) {
      marcos[id] = layout.marcoHtml({ activa: id, anio, indice, escudo: escudoRelativo, actualizado, contenido: MARCA });
      relacionados[id] = layout.relacionadoHtml(id, anio);
      anios[id] = layout.aniosHtml(id, anio, indice);
      urls[id] = rutas.urlPagina(id, anio);
    }
    const resumen = leer(`${anio}/resumen.json`);
    const deuda = leer(`${anio}/deuda.json`);
    const prestamoInversiones = leer(`${anio}/inversiones.json`).fuentes.prestamo;
    const indicadores = lecturas.calcularIndicadores({ resumen, ingresos: leer(`${anio}/ingresos.json`), deuda });
    return {
      marcos,
      relacionados,
      anios,
      urls,
      tarjetasInicio: layout.tarjetasHtml(anio),
      // Avisos sobre los préstamos (pendientes de revisión por el Ayuntamiento): se reutilizan tal cual, sin copiarlos a Python
      avisos: {
        deuda: deuda.previsto ? textos.avisoPrevisto(deuda.previsto, deuda, prestamoInversiones, anio) : textos.avisoSinPrevisto(prestamoInversiones, anio),
        inversiones: textos.avisoPrestamoInversiones(prestamoInversiones, anio),
      },
      indicadores,
      textoNivelEndeudamiento: lecturas.textoNivelEndeudamiento(indicadores),
    };
  });
}

const entornos = { raiz: entorno(ultimo, { raiz: "", ultimo: String(ultimo) }, escudo) };
for (const { anio } of indice.anios) {
  entornos[anio] = entorno(anio, { raiz: "../", anio: String(anio), ultimo: String(ultimo) }, `../${escudo}`);
}

process.stdout.write(JSON.stringify({ marca: MARCA, secciones: layout.SECCIONES, entornos }));
