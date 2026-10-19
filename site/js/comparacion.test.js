import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { emparejar, filasVista, ordenar, frase, titular, serieEvolucion, filasIndicadores, elegirPareja } from "./comparacion.js";

const leer = (r) => JSON.parse(readFileSync(new URL(r, import.meta.url), "utf8"));
const datos = (anio) => ({ anio, gastos: leer(`../data/${anio}/gastos.json`), ingresos: leer(`../data/${anio}/ingresos.json`), resumen: leer(`../data/${anio}/resumen.json`) });
const D = { 2024: datos(2024), 2025: datos(2025), 2026: datos(2026) };
const cerca = (a, b, tol = 0.01) => assert.ok(Math.abs(a - b) <= tol, `${a} ≠ ${b}`);
const buscar = (filas, clave) => filas.find((f) => f.clave === clave);

test("emparejar calcula diferencia y porcentaje con el valor actual de cada año", () => {
  const [f] = emparejar([{ k: "x", n: "X", actual: 100, anterior: 5 }], [{ k: "x", n: "X", actual: 150, anterior: 99 }], { clave: (i) => i.k, nombre: (i) => i.n });
  assert.deepEqual([f.a, f.b, f.delta, f.pct, f.estado], [100, 150, 50, 50, "sube"]);
});

test("emparejar marca nuevo, desaparece, igual y no produce NaN ni Infinity", () => {
  const op = { clave: (i) => i.k, nombre: (i) => i.n };
  const filas = emparejar(
    [{ k: "a", n: "A", actual: 10 }, { k: "d", n: "D", actual: 0 }, { k: "i", n: "I", actual: 7 }, { k: "z", n: "Z", actual: null }],
    [{ k: "b", n: "B", actual: 20 }, { k: "d", n: "D", actual: 5 }, { k: "i", n: "I", actual: 7 }, { k: "z", n: "Z", actual: undefined }],
    op,
  );
  assert.equal(buscar(filas, "a").estado, "desaparece");
  assert.equal(buscar(filas, "a").b, null);
  assert.equal(buscar(filas, "b").estado, "nuevo");
  assert.equal(buscar(filas, "b").pct, null);
  assert.equal(buscar(filas, "d").estado, "nuevo"); // de 0 a 5
  assert.equal(buscar(filas, "i").estado, "igual");
  assert.equal(buscar(filas, "z").estado, "igual");
  for (const f of filas) for (const v of [f.a, f.b, f.delta, f.pct]) assert.ok(v === null || Number.isFinite(v), `${f.clave}: ${v}`);
});

test("por habitante divide cada año entre su población y los resultados siguen siendo finitos", () => {
  const [f] = emparejar([{ k: "x", n: "X", actual: 1000 }], [{ k: "x", n: "X", actual: 1000 }], { clave: (i) => i.k, nombre: (i) => i.n, divisorA: 10, divisorB: 20 });
  assert.deepEqual([f.a, f.b, f.delta, f.pct, f.estado], [100, 50, -50, -50, "baja"]);
  const [g] = emparejar([{ k: "x", n: "X", actual: 1000 }], [{ k: "x", n: "X", actual: 1000 }], { clave: (i) => i.k, nombre: (i) => i.n, divisorA: 0, divisorB: null });
  assert.ok(g.a === null && g.b === null);
});

test("las políticas de 2024, 2025 y 2026 tienen el mismo código y nombre: la 46 solo existe en 2026", () => {
  const f = filasVista("politicas", D[2024], D[2026], "total");
  const nueva = buscar(f, "46");
  assert.equal(nueva.estado, "nuevo");
  assert.equal(nueva.nombre, "Investigación, desarrollo e innovación");
  assert.equal(f.filter((x) => x.estado === "desaparece").length, 0);
  // los nombres coinciden en los tres años para todos los códigos comunes
  for (const [x, y] of [[2024, 2025], [2025, 2026], [2024, 2026]]) {
    const nombres = (a) => Object.fromEntries(D[a].gastos.politicas.map((p) => [p.codigo, p.nombre]));
    const [n1, n2] = [nombres(x), nombres(y)];
    for (const c of Object.keys(n1)) if (c in n2) assert.equal(n1[c], n2[c], `política ${c}`);
  }
});

test("cada vista suma el total del presupuesto de cada año", () => {
  for (const [x, y] of [[2024, 2025], [2025, 2026], [2024, 2026], [2026, 2024]]) {
    for (const [vista, campo] of [["politicas", "totalGastos"], ["gastoCapitulos", "totalGastos"], ["ingresoCapitulos", "totalIngresos"]]) {
      const filas = filasVista(vista, D[x], D[y], "total");
      cerca(filas.reduce((s, f) => s + (f.a ?? 0), 0), D[x].resumen[campo], 1);
      cerca(filas.reduce((s, f) => s + (f.b ?? 0), 0), D[y].resumen[campo], 1);
    }
  }
});

test("la pareja invertida da la diferencia con el signo contrario", () => {
  const ida = buscar(filasVista("politicas", D[2024], D[2026], "total"), "33");
  const vuelta = buscar(filasVista("politicas", D[2026], D[2024], "total"), "33");
  cerca(ida.delta, -vuelta.delta);
  assert.equal(ida.a, vuelta.b);
});

test("capítulos de gastos e ingresos son los mismos en los tres años", () => {
  for (const vista of ["gastoCapitulos", "ingresoCapitulos"]) {
    const f = filasVista(vista, D[2024], D[2026], "total");
    assert.equal(f.length, 9);
    assert.ok(f.every((x) => x.a !== null && x.b !== null));
  }
});

test("por habitante usa la población de cada año", () => {
  const total = buscar(filasVista("politicas", D[2024], D[2026], "total"), "33");
  const hab = buscar(filasVista("politicas", D[2024], D[2026], "habitante"), "33");
  cerca(hab.a, total.a / D[2024].resumen.habitantes, 1e-6);
  cerca(hab.b, total.b / D[2026].resumen.habitantes, 1e-6);
});

test("ordenar: más sube, más baja, porcentaje e importe", () => {
  const filas = filasVista("politicas", D[2024], D[2026], "total");
  const sube = ordenar(filas, "sube");
  assert.ok(sube[0].delta >= sube[1].delta);
  const baja = ordenar(filas, "baja");
  assert.ok(baja[0].delta <= baja[1].delta);
  const importe = ordenar(filas, "importe");
  assert.ok(Math.max(importe[0].a ?? 0, importe[0].b ?? 0) >= Math.max(importe[1].a ?? 0, importe[1].b ?? 0));
  const pct = ordenar(filas, "pct");
  assert.ok(pct.every((f) => f.pct === null || Number.isFinite(f.pct)));
  assert.equal(filas.length, sube.length); // no pierde ni muta filas
  const nombre = ordenar(filas, "nombre");
  assert.ok(nombre[0].nombre.localeCompare(nombre[1].nombre, "es") <= 0);
});

test("frase explica el cambio con palabras llanas", () => {
  const cultura = buscar(filasVista("politicas", D[2024], D[2026], "total"), "33");
  const f = frase(cultura, 2024, 2026, { verbo: "gastar", modo: "total" });
  assert.match(f, /^En Cultura se prevé gastar /);
  assert.match(f, /en 2026/);
  assert.match(f, /que en 2024/);
  assert.doesNotMatch(f, /NaN|undefined|Infinity/);
  const nueva = buscar(filasVista("politicas", D[2024], D[2026], "total"), "46");
  assert.match(frase(nueva, 2024, 2026, { verbo: "gastar", modo: "total" }), /no tenía dinero previsto en 2024/);
  const sin = { nombre: "Algo", a: 10, b: null, delta: -10, pct: null, estado: "desaparece" };
  assert.match(frase(sin, 2024, 2026, { verbo: "gastar", modo: "total" }), /ya no tiene dinero previsto en 2026/);
  const igual = { nombre: "Algo", a: 10, b: 10, delta: 0, pct: 0, estado: "igual" };
  assert.match(frase(igual, 2024, 2026, { verbo: "ingresar", modo: "total" }), /igual que en 2024/);
  const habitante = frase({ nombre: "Cultura", a: 50, b: 80, delta: 30, pct: 60, estado: "sube" }, 2024, 2026, { verbo: "gastar", modo: "habitante" });
  assert.match(habitante, /por habitante/);
});

test("frase con pareja invertida habla de menos cuando el año posterior va primero", () => {
  const f = buscar(filasVista("politicas", D[2026], D[2024], "total"), "33");
  assert.match(frase(f, 2026, 2024, { verbo: "gastar", modo: "total" }), /menos que en 2026/);
});

test("titular resume el total de cada año y la diferencia", () => {
  const t = titular(D[2024], D[2026], "gastos", "total");
  assert.equal(t.a, D[2024].resumen.totalGastos);
  assert.equal(t.b, D[2026].resumen.totalGastos);
  cerca(t.delta, t.b - t.a);
  const h = titular(D[2024], D[2026], "ingresos", "habitante");
  cerca(h.a, D[2024].resumen.totalIngresos / D[2024].resumen.habitantes, 1e-6);
});

test("serieEvolucion da un valor por año (null si la categoría no existe ese año)", () => {
  const lista = [D[2024], D[2025], D[2026]];
  const s = serieEvolucion(lista, "politicas", "46", "total");
  assert.deepEqual(s.map((p) => p.anio), [2024, 2025, 2026]);
  assert.equal(s[0].valor, null);
  assert.equal(s[1].valor, null);
  assert.ok(s[2].valor > 0);
  const c = serieEvolucion(lista, "gastoCapitulos", "1", "habitante");
  cerca(c[1].valor, D[2025].gastos.capitulos[0].actual / D[2025].resumen.habitantes, 1e-6);
});

test("elegirPareja: por defecto los dos últimos años, ordenada como se pida y sin repetir año", () => {
  const anios = [2024, 2025, 2026];
  assert.deepEqual(elegirPareja(anios, null, null), { a: 2025, b: 2026 });
  assert.deepEqual(elegirPareja(anios, "2024", "2026"), { a: 2024, b: 2026 });
  assert.deepEqual(elegirPareja(anios, "2026", "2024"), { a: 2026, b: 2024 });
  assert.deepEqual(elegirPareja(anios, "2025", "2025"), { a: 2025, b: 2026 }); // repetido: se corrige b
  assert.deepEqual(elegirPareja(anios, "2026", "2026"), { a: 2026, b: 2025 });
  assert.deepEqual(elegirPareja(anios, "1999", "xx"), { a: 2025, b: 2026 });
  assert.deepEqual(elegirPareja([2026], null, null), { a: 2026, b: null });
});

test("filasIndicadores compara los indicadores de ambos años aunque falte el préstamo previsto", () => {
  const ind = (anio) => ({ resumen: D[anio].resumen, ingresos: D[anio].ingresos, deuda: leer(`../data/${anio}/deuda.json`) });
  const f = filasIndicadores(ind(2024), ind(2026));
  assert.ok(f.length >= 5);
  for (const x of f) {
    for (const v of [x.a, x.b, x.delta]) assert.ok(v === null || Number.isFinite(v), `${x.id}: ${v}`);
    assert.ok(["euros", "pct"].includes(x.tipo));
  }
  const nivel = f.find((x) => x.id === "deudaSobreIngresosCorrientesPct");
  assert.equal(nivel.etiqueta, "Nivel de endeudamiento (estimado)");
  cerca(nivel.a, 8.65, 0.01);
  cerca(nivel.b, 5.15, 0.01);
  const neto = f.find((x) => x.id === "ahorroNetoEstimado");
  assert.equal(neto.etiqueta, "Ahorro neto (estimado)");
  cerca(neto.a, 443545.16, 0.01);
  cerca(neto.b, 2597756.54, 0.01);
  const conPrevisto = f.find((x) => x.id === "deudaConPrevistoPorHabitante");
  if (conPrevisto) assert.ok(conPrevisto.a === null || Number.isFinite(conPrevisto.a));
});
