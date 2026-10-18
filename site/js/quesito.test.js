import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { datosQuesito, COLOR_CAPITULO } from "./quesito.js";

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
  assert.equal(items[0].nombre, "Obras e inversiones");
  assert.equal(items[0].oficial, "Inversiones reales");
});

test("los ingresos por capítulo mantienen los colores y descartan los capítulos a cero", () => {
  const caps = resumen.ingresosPorCapitulo.map((c) => (c.cap === 8 ? { ...c, y2026: 0 } : c));
  const { items } = datosQuesito(caps);
  assert.equal(items.length, 8);
  assert.ok(items.every((i) => i.valor > 0));
  const prestamos = items.find((i) => i.cap === 9);
  assert.equal(prestamos.color, COLOR_CAPITULO[9]);
  assert.ok(prestamos.pct > 31 && prestamos.pct < 32);
});
