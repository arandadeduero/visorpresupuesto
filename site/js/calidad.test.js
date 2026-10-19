// Comprobaciones sobre el código fuente de la web: avisos con file://, contraste, textos sin años fijos y ejemplos de búsqueda.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { buscar } from "./gastos-tree.js";
import { matches } from "./format.js";

const leer = (ruta) => readFileSync(new URL(ruta, import.meta.url), "utf8");
const paginas = readdirSync(new URL("../", import.meta.url)).filter((f) => f.endsWith(".html"));

test("cada página avisa con un script clásico si se abre con file://", () => {
  assert.equal(paginas.length, 11);
  for (const p of paginas) {
    const html = leer(`../${p}`);
    const clasicos = [...html.matchAll(/<script(?![^>]*type="module")(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
    assert.ok(clasicos.some((c) => c.includes('location.protocol === "file:"')), `${p} sin aviso para file://`);
  }
});

const luminancia = (hex) => {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const contraste = (a, b) => {
  const [x, y] = [luminancia(a), luminancia(b)].sort((m, n) => n - m);
  return (x + 0.05) / (y + 0.05);
};

test("el azul de los textos y enlaces cumple contraste AA (4,5:1) sobre los fondos de la web", () => {
  const css = leer("../css/styles.css");
  const azul = css.match(/--azul-texto:\s*(#[0-9a-fA-F]{6})/)?.[1];
  assert.ok(azul, "falta --azul-texto");
  for (const fondo of ["#ffffff", "#e9f4f9", "#fff8e6"]) assert.ok(contraste(azul, fondo) >= 4.5, `${azul} sobre ${fondo}: ${contraste(azul, fondo).toFixed(2)}`);
  assert.match(css, /a\s*\{[^}]*color:\s*var\(--azul-texto\)/);
});

test("el foco visible se distingue sobre fondo claro y sobre la cabecera roja", () => {
  const css = leer("../css/styles.css");
  const regla = css.match(/:focus-visible\s*\{([^}]*)\}/)?.[1] ?? "";
  assert.ok(contraste("#3c3c3c", "#ffffff") >= 3);
  assert.match(regla, /outline:\s*3px solid var\(--gris-oscuro\)/);
  assert.match(regla, /box-shadow:[^;]*#fff/);
});

test("los textos de la interfaz no llevan años fijos (se derivan del año elegido)", () => {
  const ficheros = readdirSync(new URL("./", import.meta.url)).filter((f) => f.endsWith(".js") && !f.endsWith(".test.js"));
  const sueltos = [];
  for (const f of ficheros) {
    leer(`./${f}`).split("\n").forEach((linea, i) => {
      if (/^\s*(\/\/|\*|\/\*)/.test(linea)) return;
      if (/(?<![\w.])20\d\d(?!\w)/.test(linea)) sueltos.push(`${f}:${i + 1}`);
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
