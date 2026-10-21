// Rendimiento: cada página pide solo los JSON que usa, y la portada no espera a gastos.json (el más pesado) para pintar.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const leer = (f) => readFileSync(new URL(`./${f}`, import.meta.url), "utf8");

test("la portada pinta con resumen.json y pide gastos.json después, solo para la tarjeta «¿Cuánto gasta…?»", () => {
  const home = leer("home.js");
  assert.doesNotMatch(home, /Promise\.all\(\[[^\]]*"gastos"/);
  const pinta = home.indexOf("main.innerHTML =");
  const pide = home.indexOf('load("gastos")');
  assert.ok(pinta > 0 && pide > pinta, "gastos.json se pide después de pintar la portada");
  assert.equal(home.match(/load\("gastos"\)/g).length, 1);
  // la tarjeta reserva su altura con una clase (sin estilos en línea) y el botón espera a los datos
  assert.match(home, /class="destacado-caja"/);
  assert.match(home, /id="otra" disabled/);
});

test("los datos de cada página se piden una sola vez (caché de data.js) y getIndex no se pide aparte en las páginas", () => {
  const data = leer("data.js");
  assert.match(data, /leerUnaVez\(urlDatos\("index\.json"\)\)/);
  assert.match(data, /export const loadData = .*leerUnaVez/);
});
