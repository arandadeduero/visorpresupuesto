import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseImporte, repartoAportacion, calcularIndicadores, situacionEndeudamiento, textoNivelEndeudamiento, UMBRAL_AUTORIZACION_PCT, UMBRAL_PROHIBICION_PCT } from "./lecturas.js";

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

test("nivel de endeudamiento estimado (art. 53 TRLRHL): ingresos corrientes = capítulos 1 a 5, deuda viva de los préstamos existentes, en los tres años", () => {
  const esperado = {
    2024: { ic: 37538146.94, viva: 3245446.74, pct: 8.65, conPrevisto: null },
    2025: { ic: 38118061.71, viva: 2713393.77, pct: 7.12, conPrevisto: 35.98 },
    2026: { ic: 42365106.61, viva: 2181340.81, pct: 5.15, conPrevisto: 31.11 },
  };
  for (const [anio, e] of Object.entries(esperado)) {
    const d = (n) => leer(`../data/${anio}/${n}.json`);
    const i = calcularIndicadores({ resumen: d("resumen"), ingresos: d("ingresos"), deuda: d("deuda") });
    cerca(i.ingresosCorrientes, e.ic);
    cerca(i.deudaViva, e.viva);
    cerca(i.deudaSobreIngresosCorrientesPct, e.pct, 0.01);
    if (e.conPrevisto === null) assert.equal(i.deudaConPrevistoSobreIngresosCorrientesPct, null);
    else cerca(i.deudaConPrevistoSobreIngresosCorrientesPct, e.conPrevisto, 0.01);
    // En los tres años, con y sin el préstamo previsto, se está muy por debajo del 75 %.
    assert.equal(situacionEndeudamiento(i.deudaConPrevistoSobreIngresosCorrientesPct ?? i.deudaSobreIngresosCorrientesPct), "bajo75");
  }
});

test("situacionEndeudamiento aplica los umbrales del 75 % y del 110 % sin inventar nada cuando falta el dato", () => {
  assert.equal(UMBRAL_AUTORIZACION_PCT, 75);
  assert.equal(UMBRAL_PROHIBICION_PCT, 110);
  assert.equal(situacionEndeudamiento(null), null);
  assert.equal(situacionEndeudamiento(NaN), null);
  assert.equal(situacionEndeudamiento(0), "bajo75");
  assert.equal(situacionEndeudamiento(75), "bajo75"); // «no exceda del 75 %»
  assert.equal(situacionEndeudamiento(75.01), "entre75y110");
  assert.equal(situacionEndeudamiento(110), "entre75y110"); // «exceda del 110 %» es estrictamente mayor
  assert.equal(situacionEndeudamiento(110.01), "sobre110");
});

test("textoNivelEndeudamiento explica la regla legal en llano, sin cifras no respaldadas por la ley", () => {
  const d = (n) => leer(`../data/2026/${n}.json`);
  const i = calcularIndicadores({ resumen: d("resumen"), ingresos: d("ingresos"), deuda: d("deuda") });
  const t = textoNivelEndeudamiento(i);
  assert.match(t, /capítulos 1 a 5/);
  assert.match(t, /75 %/);
  assert.match(t, /110 %/);
  assert.match(t, /31,1 %/); // con el préstamo previsto
  assert.match(t, /por debajo del 75 %/);
  assert.match(t, /liquidados del año anterior/);
  assert.doesNotMatch(t, /40 ?%/);
  // sin préstamo previsto (2024) no se menciona
  const d24 = (n) => leer(`../data/2024/${n}.json`);
  const t24 = textoNivelEndeudamiento(calcularIndicadores({ resumen: d24("resumen"), ingresos: d24("ingresos"), deuda: d24("deuda") }));
  assert.doesNotMatch(t24, /préstamo previsto/);
  assert.match(t24, /por debajo del 75 %/);
  // superando los umbrales
  assert.match(textoNivelEndeudamiento({ ...i, deudaConPrevistoSobreIngresosCorrientesPct: 90 }), /necesitaría autorización/);
  assert.match(textoNivelEndeudamiento({ ...i, deudaConPrevistoSobreIngresosCorrientesPct: 120 }), /no podría concertar/);
  assert.doesNotMatch(textoNivelEndeudamiento({ ...i, deudaSobreIngresosCorrientesPct: null, deudaConPrevisto: null }), /NaN|undefined|null/);
});

test("ahorro neto estimado =ahorro bruto menos la carga de los préstamos actuales, en los tres años", () => {
  const esperado = { 2024: [443545.16, 1.18], 2025: [764778.16, 2.01], 2026: [2597756.54, 6.13] };
  for (const [anio, [neto, pctNeto]] of Object.entries(esperado)) {
    const d = (n) => leer(`../data/${anio}/${n}.json`);
    const i = calcularIndicadores({ resumen: d("resumen"), ingresos: d("ingresos"), deuda: d("deuda") });
    cerca(i.ahorroNetoEstimado, neto);
    cerca(i.ahorroNetoEstimadoPct, pctNeto, 0.01);
  }
});
