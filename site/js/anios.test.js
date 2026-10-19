// Cada año publicado (site/data/index.json) se puede leer con las mismas funciones, sin NaN y sin suponer un año concreto.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { buildTree, buscar } from "./gastos-tree.js";
import { mayoresCambios, porHabitante } from "./insights.js";
import { calcularIndicadores, repartoAportacion } from "./lecturas.js";
import { datosQuesito } from "./quesito.js";

const leer = (r) => JSON.parse(readFileSync(new URL(r, import.meta.url), "utf8"));
const indice = leer("../data/index.json");
const ANIOS = indice.anios.map((a) => a.anio);
const datos = (anio, nombre) => leer(`../data/${anio}/${nombre}.json`);
const cerca = (a, b, tol = 0.01) => assert.ok(Math.abs(a - b) <= tol, `${a} ≠ ${b}`);
const sinNaN = (valor, ruta = "") => {
  if (typeof valor === "number") assert.ok(Number.isFinite(valor), `${ruta} no es un número finito`);
  else if (Array.isArray(valor)) valor.forEach((v, i) => sinNaN(v, `${ruta}[${i}]`));
  else if (valor && typeof valor === "object") Object.entries(valor).forEach(([k, v]) => sinNaN(v, `${ruta}.${k}`));
};

test("el índice publica 2024, 2025 y 2026 y el año por defecto es el último", () => {
  assert.deepEqual(ANIOS, [2024, 2025, 2026]);
  assert.equal(indice.ultimo, 2026);
  assert.equal(readdirSync(new URL("../data/", import.meta.url)).filter((f) => /^\d{4}$/.test(f)).length, ANIOS.length);
});

for (const anio of ANIOS) {
  test(`${anio}: los seis ficheros son números finitos y el árbol de gastos suma el presupuesto`, () => {
    for (const n of ["resumen", "ingresos", "gastos", "inversiones", "subvenciones", "deuda"]) sinNaN(datos(anio, n), `${anio}/${n}`);
    const gastos = datos(anio, "gastos");
    const resumen = datos(anio, "resumen");
    for (const modo of ["politica", "capitulo"]) {
      const raiz = buildTree(gastos, modo);
      cerca(raiz.reduce((s, n) => s + n.actual, 0), resumen.totalGastos, 1);
    }
  });

  test(`${anio}: el árbol no inventa variaciones donde falta el año anterior`, () => {
    const gastos = datos(anio, "gastos");
    const sin = new Set(gastos.sinAnterior);
    const raiz = buildTree(gastos, "politica");
    const hojas = (n) => (n.hijos ? n.hijos.flatMap(hojas) : [n]);
    for (const pol of raiz) {
      const conInversion = hojas(pol).some((h) => h.anterior === null);
      assert.equal(pol.anterior === null, conInversion, pol.nombre);
      if (sin.size === 0) assert.ok(typeof pol.anterior === "number", pol.nombre);
    }
    // por capítulo el nivel superior usa los créditos de A1, que siempre existen
    for (const cap of buildTree(gastos, "capitulo")) assert.ok(typeof cap.anterior === "number", cap.nombre);
  });

  test(`${anio}: cambios del año anterior y quesitos sin NaN`, () => {
    const gastos = datos(anio, "gastos");
    const ingresos = datos(anio, "ingresos");
    const comparables = gastos.politicas.filter((p) => p.anterior !== null);
    for (const lista of [comparables, ingresos.capitulos.flatMap((c) => c.conceptos)]) {
      const { suben, bajan } = mayoresCambios(lista, 5);
      sinNaN([suben.map((x) => [x.delta, x.pct ?? 0]), bajan.map((x) => [x.delta, x.pct ?? 0])]);
      assert.ok(suben.every((x) => x.delta > 0) && bajan.every((x) => x.delta < 0));
    }
    const { items, total } = datosQuesito(datos(anio, "resumen").gastosPorCapitulo);
    cerca(items.reduce((s, i) => s + i.pct, 0), 100, 1e-6);
    assert.ok(total > 0);
  });

  test(`${anio}: los indicadores no producen NaN y la calculadora reparte lo aportado`, () => {
    const i = calcularIndicadores({ resumen: datos(anio, "resumen"), ingresos: datos(anio, "ingresos"), deuda: datos(anio, "deuda") });
    sinNaN(i);
    cerca(repartoAportacion(1000, datos(anio, "gastos").politicas).reduce((s, x) => s + x.importe, 0), 1000);
  });

  test(`${anio}: buscar en gastos devuelve filas con importes`, () => {
    const filas = buscar(datos(anio, "gastos"), "energía");
    assert.ok(filas.length > 0);
    assert.ok(filas.every((f) => Number.isFinite(f.actual)));
  });
}

test("indicadores de 2024 y 2025 con las cifras de su Excel (A1 y A13.1)", () => {
  const ind = (a) => calcularIndicadores({ resumen: datos(a, "resumen"), ingresos: datos(a, "ingresos"), deuda: datos(a, "deuda") });
  const i24 = ind(2024);
  cerca(i24.ingresosCorrientes, 37538146.94); // «Ingresos 1-5» de A1
  cerca(i24.gastosCorrientes, 14908290.5 + 19550670 + 1955748);
  cerca(i24.ahorroBruto, 37538146.94 - 36414708.5);
  cerca(i24.deudaViva, 3245446.74);
  cerca(i24.deudaPorHabitante, 3245446.74 / 33757, 0.01);
  cerca(i24.cargaFinanciera, 147840.3 + 532052.98, 0.02);
  // 2024 no tiene préstamo previsto: no se calcula nada «con previsto»
  assert.equal(i24.deudaConPrevisto, null);
  assert.equal(i24.deudaConPrevistoPorHabitante, null);
  assert.equal(i24.deudaConPrevistoSobreIngresosCorrientesPct, null);

  const i25 = ind(2025);
  cerca(i25.ingresosCorrientes, 38118061.71); // «Ingresos 1-5» de A1
  cerca(i25.ahorroBruto, 38118061.71 - (15562398.5 + 19430030 + 1727680));
  cerca(i25.deudaViva, 2713393.77, 0.02);
  cerca(i25.deudaConPrevisto, 13713393.77, 0.02);
  cerca(i25.deudaPorHabitante, 2713393.77 / 33956, 0.01);
});

test("las personas por habitante usan la población de cada año", () => {
  assert.equal(datos(2024, "resumen").habitantes, 33757);
  assert.equal(datos(2025, "resumen").habitantes, 33956);
  cerca(porHabitante(datos(2024, "resumen").totalGastos, 33757), 49800478.98 / 33757, 1e-6);
});
