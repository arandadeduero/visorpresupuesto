import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { datosQuesito, datosArticulos, tonoArticulo, articulosDeIngresos, COLOR_CAPITULO } from "./quesito.js";

const leer = (r) => JSON.parse(readFileSync(new URL(r, import.meta.url), "utf8"));
const resumen = leer("../data/2026/resumen.json");

test("cada capítulo tiene un color propio y estable", () => {
  const colores = Object.values(COLOR_CAPITULO);
  assert.equal(colores.length, 9);
  assert.equal(new Set(colores).size, 9);
  assert.ok(colores.every((c) => /^#[0-9a-f]{6}$/i.test(c)));
  assert.equal(COLOR_CAPITULO[6], "#0083c1"); // obras e inversiones: el azul de la portada
  assert.equal(COLOR_CAPITULO[2], "#f5a800"); // servicios
  assert.equal(COLOR_CAPITULO[1], "#ce0e2d"); // personal
});

test("los gastos por capítulo se ordenan de mayor a menor y suman el 100 %", () => {
  const { items, total } = datosQuesito(resumen.gastosPorCapitulo);
  assert.ok(Math.abs(total - 64280861.35) < 1);
  assert.deepEqual(items.map((i) => i.cap).slice(0, 3), [6, 2, 1]);
  assert.ok(items.every((x, i) => i === 0 || items[i - 1].valor >= x.valor));
  assert.ok(Math.abs(items.reduce((s, i) => s + i.pct, 0) - 100) < 0.01);
  assert.equal(items[0].color, COLOR_CAPITULO[6]);
  assert.equal(items[0].nombre, "Cap 6 - Obras e inversiones");
  assert.equal(items[0].oficial, "Inversiones reales");
});

test("los ingresos por capítulo mantienen los colores y descartan los capítulos a cero", () => {
  const caps = resumen.ingresosPorCapitulo.map((c) => (c.cap === 8 ? { ...c, actual: 0 } : c));
  const { items } = datosQuesito(caps);
  assert.equal(items.length, 8);
  assert.ok(items.every((i) => i.valor > 0));
  const prestamos = items.find((i) => i.cap === 9);
  assert.equal(prestamos.color, COLOR_CAPITULO[9]);
  assert.ok(prestamos.pct > 31 && prestamos.pct < 32);
});

// ----- Vista por artículos -----
const ANIOS = [2024, 2025, 2026];
const ingresosDe = (a) => leer(`../data/${a}/ingresos.json`);
const gastosDe = (a) => leer(`../data/${a}/gastos.json`);

test("los tonos de un capítulo empiezan en su color, son colores válidos y no se repiten", () => {
  const tonos = [0, 1, 2, 3, 4, 5].map((i) => tonoArticulo("#0083c1", i));
  assert.equal(tonos[0], "#0083c1");
  assert.ok(tonos.every((t) => /^#[0-9a-f]{6}$/.test(t)));
  assert.equal(new Set(tonos).size, tonos.length);
});

for (const anio of ANIOS) {
  test(`${anio}: los artículos de ingresos suman el total, se agrupan por capítulo y cada uno lleva el color de su familia`, () => {
    const d = ingresosDe(anio);
    const { items, total, grupos } = datosArticulos(d.capitulos, articulosDeIngresos(d));
    assert.ok(Math.abs(items.reduce((s, i) => s + i.valor, 0) - total) < 0.01);
    assert.ok(Math.abs(items.reduce((s, i) => s + i.pct, 0) - 100) < 0.01);
    assert.ok(items.every((i) => i.valor > 0 && Number.isFinite(i.pct) && i.nombre && i.color));
    const caps = items.map((i) => i.cap);
    assert.deepEqual(caps, grupos.flatMap((g) => g.items.map((i) => i.cap)));
    assert.ok(grupos.every((g, i) => i === 0 || grupos[i - 1].valor >= g.valor));
    for (const g of grupos) assert.ok(g.items.every((i) => i.cap === g.cap));
  });

  test(`${anio}: los artículos de gastos suman el total`, () => {
    const d = gastosDe(anio);
    const { items, total } = datosArticulos(d.capitulos, d.articulos);
    assert.ok(Math.abs(total - d.capitulos.reduce((s, c) => s + c.actual, 0)) < 1);
    assert.ok(Math.abs(items.reduce((s, i) => s + i.valor, 0) - total) < 0.01);
  });
}

test("2026: los préstamos recibidos (artículo 91) son el 31,4 % de los ingresos y salen con su nombre", () => {
  const d = ingresosDe(2026);
  const { items } = datosArticulos(d.capitulos, articulosDeIngresos(d));
  const prestamos = items.find((i) => i.codigo === "91");
  assert.equal(prestamos.nombre, "Préstamos recibidos");
  assert.equal(prestamos.valor, 20161623.64);
  assert.ok(prestamos.pct > 31 && prestamos.pct < 32);
  assert.equal(prestamos.color, COLOR_CAPITULO[9]);
});

test("los artículos pequeños de un capítulo se agrupan en «Otros artículos del Cap N», una sola vez por capítulo", () => {
  const d = ingresosDe(2026);
  const { items, grupos } = datosArticulos(d.capitulos, articulosDeIngresos(d));
  const otros = items.filter((i) => i.otros);
  assert.ok(otros.length > 0);
  assert.ok(otros.every((o) => /^Otros artículos del Cap \d$/.test(o.nombre)));
  for (const g of grupos) assert.ok(g.items.filter((i) => i.otros).length <= 1);
  assert.ok(items.length <= 20);
});

test("los capítulos a cero no producen porciones vacías", () => {
  const d = gastosDe(2026);
  const caps = d.capitulos.map((c) => (c.cap === 8 ? { ...c, actual: 0 } : c));
  const arts = d.articulos.map((a) => (a.cap === 8 ? { ...a, actual: 0 } : a));
  const { items } = datosArticulos(caps, arts);
  assert.ok(items.every((i) => i.valor > 0) && !items.some((i) => i.cap === 8));
});

test("la leyenda de capítulos es una tabla con cabecera (ordenable): capítulo, % e importe", async () => {
  const { tablaLeyendaCapitulos } = await import("./quesito.js");
  const { items } = datosQuesito(resumen.ingresosPorCapitulo);
  const html = tablaLeyendaCapitulos(items);
  assert.match(html, /<table class="datos/);
  const cabeceras = [...html.matchAll(/<th[^>]*>(.*?)<\/th>/g)].map((m) => m[1].replace(/<[^>]+>/g, "").trim());
  assert.deepEqual(cabeceras, ["Capítulo", "% del total", "Importe"]);
  assert.equal([...html.matchAll(/<tbody>[\s\S]*<\/tbody>/g)][0][0].split("<tr").length - 1, items.length);
  for (const i of items) assert.ok(html.includes(`background:${i.color}`), i.nombre);
  assert.ok(html.includes("Cap 9 - Préstamos"));
  assert.match(html, /31,4\s%/);
});

test("la leyenda de artículos es una tabla plana con capítulo, artículo, % e importe", async () => {
  const { tablaLeyendaArticulos, datosArticulos, articulosDeIngresos } = await import("./quesito.js");
  const datos = datosArticulos(resumen.ingresosPorCapitulo, articulosDeIngresos(leer("../data/2026/ingresos.json")));
  const html = tablaLeyendaArticulos(datos.grupos);
  const cabeceras = [...html.matchAll(/<th[^>]*>(.*?)<\/th>/g)].map((m) => m[1].replace(/<[^>]+>/g, "").trim());
  assert.deepEqual(cabeceras, ["Capítulo", "Artículo", "% del total", "Importe"]);
  const filas = html.split("<tbody>")[1].split("<tr").length - 1;
  assert.equal(filas, datos.items.length);
  assert.ok(html.includes("Préstamos recibidos"));
  assert.doesNotMatch(html, /leyenda-agrupada|<ul/);
});

test("las leyendas ya no son listas: quesito.js solo pinta tablas", () => {
  const fuente = readFileSync(new URL("./quesito.js", import.meta.url), "utf8");
  assert.doesNotMatch(fuente, /leyenda-quesito|leyenda-agrupada|<ul/);
});
