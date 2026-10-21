// Comprobaciones sobre el código fuente de la web: avisos con file://, contraste, textos sin años fijos y ejemplos de búsqueda.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { buscar } from "./gastos-tree.js";
import { matches } from "./format.js";

const leer = (ruta) => readFileSync(new URL(ruta, import.meta.url), "utf8");
const paginas = readdirSync(new URL("../", import.meta.url)).filter((f) => f.endsWith(".html"));

test("cada página avisa con un script clásico (fichero propio, no en línea) si se abre con file://", () => {
  assert.equal(paginas.length, 12);
  const aviso = leer("./aviso-file.js");
  assert.ok(aviso.includes('location.protocol === "file:"'));
  for (const p of paginas) {
    const html = leer(`../${p}`);
    assert.ok(/<script src="js\/aviso-file\.js"><\/script>/.test(html), `${p} sin aviso para file://`);
    assert.doesNotMatch(html, /<script(?![^>]*\bsrc=)[^>]*>/, `${p} tiene un script en línea`);
  }
});

test("los textos de la interfaz no llevan años fijos (se derivan del año elegido)", () => {
  const ficheros = readdirSync(new URL("./", import.meta.url)).filter((f) => f.endsWith(".js") && !f.endsWith(".test.js"));
  const sueltos = [];
  for (const f of ficheros) {
    leer(`./${f}`).split("\n").forEach((linea, i) => {
      if (/^\s*(\/\/|\*|\/\*)/.test(linea)) return;
      // El «/» delante deja pasar las citas de normas («Ley 17/2012») y se ignoran los enlaces al BOE (BOE-A-2004-4214):
      // no son años de presupuesto.
      if (linea.includes("boe.es")) return;
      if (/(?<![\w./])20\d\d(?!\w)/.test(linea)) sueltos.push(`${f}:${i + 1}`);
    });
  }
  assert.deepEqual(sueltos, []);
});

test("las claves de los datos no llevan años (anterior/actual), para que sirvan en cualquier ejercicio", () => {
  const ficheros = readdirSync(new URL("./", import.meta.url)).filter((f) => f.endsWith(".js"));
  for (const f of ficheros) assert.doesNotMatch(leer(`./${f}`), /\b(y20\d\d|total20\d\d|totalGastos20\d\d)\b/, `${f} usa una clave con año`);
});

const ANIOS = JSON.parse(leer("../data/index.json")).anios.map((a) => a.anio);

for (const anio of ANIOS) {
  test(`los ejemplos que sugieren los buscadores devuelven resultados en ${anio}`, () => {
    const ejemplos = (fichero) => leer(fichero).match(/placeholder="Por ejemplo: ([^"]+)"/)[1].replace("…", "").split(",").map((s) => s.trim()).filter(Boolean);
    const gastos = JSON.parse(leer(`../data/${anio}/gastos.json`));
    for (const e of ejemplos("./gastos.js")) assert.ok(buscar(gastos, e).length > 0, `gastos: «${e}» sin resultados`);
    const ingresos = JSON.parse(leer(`../data/${anio}/ingresos.json`));
    const conceptos = ingresos.capitulos.flatMap((c) => c.conceptos);
    for (const e of ejemplos("./ingresos.js")) assert.ok(conceptos.some((x) => matches(x.nombre, e)), `ingresos: «${e}» sin resultados`);
    const subv = JSON.parse(leer(`../data/${anio}/subvenciones.json`));
    for (const e of ejemplos("./subvenciones.js")) assert.ok(subv.entidades.some((x) => matches(x.entidad, e)), `subvenciones: «${e}» sin resultados`);
  });
}

test("la muestra de color de la leyenda de los quesitos tiene estilo y las leyendas ya no usan listas", () => {
  const css = leer("../css/styles.css");
  assert.match(css, /\.muestra\s*\{[^}]*width:\s*12px/);
  assert.doesNotMatch(css, /leyenda-quesito|leyenda-agrupada|grupo-cab/);
});

test("los gráficos se vuelven a dibujar cuando termina de cargar la tipografía", () => {
  const fuente = leer("./charts.js");
  assert.match(fuente, /document\.fonts\??\.ready/);
});

test("el relleno de las barras es un bloque: un <span> en línea ignoraría su ancho y la barra saldría vacía", () => {
  const css = leer("../css/styles.css").replace(/\/\*[\s\S]*?\*\//g, "");
  const reglas = (selector) =>
    [...css.matchAll(/([^{}]+)\{([^}]*)\}/g)]
      .filter((m) => m[1].split(",").some((x) => x.trim() === selector))
      .map((m) => m[2])
      .join(";");
  for (const sel of [".fila .relleno", ".par-barra .relleno", ".mini-barra i"]) {
    assert.match(reglas(sel), /display:\s*block/, `${sel} debe ser display:block`);
  }
});
