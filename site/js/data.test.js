// Carga de datos: cada JSON se pide una sola vez (getIndex se llama desde varios sitios) y la guía sale de un JSON compartido.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const peticiones = [];
globalThis.fetch = async (ruta) => {
  peticiones.push(ruta);
  if (ruta.includes("falla")) return { ok: false };
  return { ok: true, json: async () => ({ anios: [{ anio: 2026, tipo: "inicial" }], ultimo: 2026 }) };
};
globalThis.location = { search: "", protocol: "https:" };

const { getIndex, getYear, loadData, getGuiaTerminos, urlDatos } = await import("./data.js");

test("getIndex pide index.json una sola vez aunque se llame varias veces, también a la vez", async () => {
  const [a, b] = await Promise.all([getIndex(), getIndex()]);
  await getYear();
  await getIndex();
  assert.equal(a, b);
  assert.equal(peticiones.filter((r) => r.endsWith("index.json")).length, 1);
});

test("loadData cachea por año y fichero", async () => {
  await loadData(2026, "resumen");
  await loadData(2026, "resumen");
  await loadData(2026, "gastos");
  assert.equal(peticiones.filter((r) => r.includes("/resumen.json")).length, 1);
  assert.equal(peticiones.filter((r) => r.includes("/gastos.json")).length, 1);
});

test("un error no se queda en la caché: el siguiente intento vuelve a pedir", async () => {
  await assert.rejects(loadData(2026, "falla"));
  await assert.rejects(loadData(2026, "falla"));
  assert.equal(peticiones.filter((r) => r.includes("falla")).length, 2);
});

test("los términos de la guía se leen de data/guia-terminos.json", async () => {
  assert.equal(urlDatos("guia-terminos.json"), "data/guia-terminos.json");
  await getGuiaTerminos();
  assert.ok(peticiones.includes("data/guia-terminos.json"));
});

test("guia.js no lleva los textos: los lee del JSON compartido", () => {
  const guia = readFileSync(new URL("./guia.js", import.meta.url), "utf8");
  assert.match(guia, /getGuiaTerminos/);
  assert.doesNotMatch(guia, /Lo que el Ayuntamiento prevé ingresar y gastar/);
  const terminos = JSON.parse(readFileSync(new URL("../data/guia-terminos.json", import.meta.url), "utf8"));
  assert.ok(terminos.length >= 20 && terminos.every((t) => t.termino && t.definicion));
});
