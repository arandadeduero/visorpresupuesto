// Saca de los módulos JS de la web lo que el build necesita para el HTML estático, para no repetirlo en Python:
// el marco (cabecera, menú, pie), el bloque «Relacionado», las tarjetas de la portada, el menú y los indicadores.
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
const lecturas = await importar("lecturas.js");
const textos = await importar("deuda-texto.js");
const indice = leer("index.json");
const ultimo = indice.ultimo;
const MARCA = "<!--CONTENIDO-->";

const marcos = {};
const relacionados = {};
for (const [id] of layout.SECCIONES) {
  marcos[id] = layout.marcoHtml({ activa: id, anio: ultimo, indice, escudo, actualizado, contenido: MARCA, enlazarAnio: false });
  relacionados[id] = layout.relacionadoHtml(id, null);
}

const indicadores = lecturas.calcularIndicadores({
  resumen: leer(`${ultimo}/resumen.json`),
  ingresos: leer(`${ultimo}/ingresos.json`),
  deuda: leer(`${ultimo}/deuda.json`),
});

// Avisos sobre los préstamos (pendientes de revisión por el Ayuntamiento): se reutilizan tal cual, sin copiarlos a Python
const deuda = leer(`${ultimo}/deuda.json`);
const prestamoInversiones = leer(`${ultimo}/inversiones.json`).fuentes.prestamo;
const avisos = {
  deuda: deuda.previsto ? textos.avisoPrevisto(deuda.previsto, deuda, prestamoInversiones, ultimo) : textos.avisoSinPrevisto(prestamoInversiones, ultimo),
  inversiones: textos.avisoPrestamoInversiones(prestamoInversiones, ultimo),
};

process.stdout.write(JSON.stringify({
  marca: MARCA,
  secciones: layout.SECCIONES,
  marcos,
  relacionados,
  tarjetasInicio: layout.tarjetasHtml(null),
  avisos,
  indicadores,
  textoNivelEndeudamiento: lecturas.textoNivelEndeudamiento(indicadores),
}));
