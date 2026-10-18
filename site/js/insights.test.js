import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { porHabitante, mayoresCambios, destacar } from "./insights.js";

const leer = (r) => JSON.parse(readFileSync(new URL(r, import.meta.url), "utf8"));
const gastos = leer("../data/2026/gastos.json");
const ingresos = leer("../data/2026/ingresos.json");
const resumen = leer("../data/2026/resumen.json");

test("porHabitante divide por la población y no revienta sin ella", () => {
  assert.equal(porHabitante(33956, 33956), 1);
  assert.ok(Math.abs(porHabitante(resumen.totalGastos, resumen.habitantes) - 1893) < 1);
  assert.equal(porHabitante(1000, 0), null);
  assert.equal(porHabitante(1000, null), null);
  assert.equal(porHabitante(null, 100), null);
});

test("mayoresCambios separa lo que sube de lo que baja, por importe, sin NaN", () => {
  const items = [
    { nombre: "a", anterior: 100, actual: 150 },
    { nombre: "b", anterior: 0, actual: 80 },
    { nombre: "c", anterior: 500, actual: 100 },
    { nombre: "d", anterior: 10, actual: 10 },
    { nombre: "e", anterior: null, actual: null },
    { nombre: "f", anterior: 50, actual: 45 },
  ];
  const { suben, bajan } = mayoresCambios(items, 2);
  assert.deepEqual(suben.map((x) => x.nombre), ["b", "a"]);
  assert.deepEqual(bajan.map((x) => x.nombre), ["c", "f"]);
  assert.equal(suben[0].pct, null);
  assert.equal(suben[1].delta, 50);
  assert.ok(Math.abs(bajan[0].pct - -80) < 1e-9);
  assert.equal(mayoresCambios([], 5).suben.length, 0);
});

test("mayoresCambios con los gastos reales de 2026", () => {
  const { suben, bajan } = mayoresCambios(gastos.programas, 5);
  assert.equal(suben.length, 5);
  assert.equal(bajan.length, 5);
  assert.ok(suben.every((x) => x.delta > 0) && bajan.every((x) => x.delta < 0));
  assert.ok(suben[0].delta >= suben[4].delta && bajan[0].delta <= bajan[4].delta);
  const conceptos = ingresos.capitulos.flatMap((c) => c.conceptos);
  assert.ok(mayoresCambios(conceptos, 3).suben.length === 3);
});

test("destacar resume una política: importe, euros por vecino y porcentaje", () => {
  const cultura = gastos.politicas.find((p) => p.nombre === "Cultura");
  const d = destacar(cultura, resumen.totalGastos, resumen.habitantes);
  assert.equal(d.nombre, "Cultura");
  assert.equal(d.importe, cultura.actual);
  assert.ok(Math.abs(d.porHabitante - cultura.actual / 33956) < 1e-9);
  assert.ok(d.pct > 10 && d.pct < 12);
  assert.equal(destacar(cultura, resumen.totalGastos, 0).porHabitante, null);
});
