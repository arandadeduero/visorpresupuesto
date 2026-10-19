import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseImporte, repartoAportacion, calcularIndicadores } from "./lecturas.js";

const leer = (r) => JSON.parse(readFileSync(new URL(r, import.meta.url), "utf8"));
const gastos = leer("../data/2026/gastos.json");
const ingresos = leer("../data/2026/ingresos.json");
const resumen = leer("../data/2026/resumen.json");
const deuda = leer("../data/2026/deuda.json");
const cerca = (a, b, tol = 0.01) => assert.ok(Math.abs(a - b) <= tol, `${a} ≠ ${b}`);

test("parseImporte entiende los formatos españoles y no revienta con basura", () => {
  assert.equal(parseImporte("350"), 350);
  assert.equal(parseImporte("1.234,56"), 1234.56);
  assert.equal(parseImporte("1234,5 €"), 1234.5);
  assert.equal(parseImporte("  "), 0);
  assert.equal(parseImporte("abc"), 0);
  assert.equal(parseImporte("-40"), 0);
  assert.equal(parseImporte(null), 0);
});

test("repartoAportacion reparte lo que pagas en proporción al gasto de cada política", () => {
  const total = gastos.politicas.reduce((s, p) => s + p.actual, 0);
  const reparto = repartoAportacion(1000, gastos.politicas);
  cerca(reparto.reduce((s, x) => s + x.importe, 0), 1000);
  assert.ok(reparto.every((x, i) => i === 0 || reparto[i - 1].importe >= x.importe));
  const cultura = reparto.find((x) => x.nombre === "Cultura");
  cerca(cultura.importe, (1000 * gastos.politicas.find((p) => p.nombre === "Cultura").actual) / total, 1e-6);
  assert.deepEqual(repartoAportacion(0, gastos.politicas), []);
  assert.deepEqual(repartoAportacion(NaN, gastos.politicas), []);
});

test("calcularIndicadores con las cifras de 2026", () => {
  const i = calcularIndicadores({ resumen, ingresos, deuda });
  cerca(i.ingresosCorrientes, 42365106.61);
  cerca(i.gastosCorrientes, 39169918.5); // personal + servicios + ayudas, sin intereses
  cerca(i.ahorroBruto, 3195188.11);
  cerca(i.ahorroBrutoPct, 7.54, 0.01);
  cerca(i.impuestosPorHabitante, (16600000 + 900000) / 33956, 0.01);
  cerca(i.impuestosYTasasPorHabitante, (16600000 + 900000 + 8359410) / 33956, 0.01);
  cerca(i.deudaViva, 2181340.81);
  cerca(i.deudaPorHabitante, 2181340.81 / 33956, 0.01);
  cerca(i.deudaConPrevistoPorHabitante, 13181340.81 / 33956, 0.01);
  cerca(i.deudaSobreIngresosCorrientesPct, (2181340.81 / 42365106.61) * 100, 0.01);
  cerca(i.deudaConPrevistoSobreIngresosCorrientesPct, (13181340.81 / 42365106.61) * 100, 0.01);
  cerca(i.dependenciaTransferenciasPct, (14419582.61 / 42365106.61) * 100, 0.01);
  cerca(i.cargaFinanciera, 597431.57);
  cerca(i.cargaFinancieraPct, (597431.57 / 42365106.61) * 100, 0.01);
});

test("calcularIndicadores sin población no inventa importes por habitante", () => {
  const i = calcularIndicadores({ resumen: { ...resumen, habitantes: 0 }, ingresos, deuda });
  assert.equal(i.impuestosPorHabitante, null);
  assert.equal(i.deudaPorHabitante, null);
  assert.ok(i.ahorroBruto > 0);
});
