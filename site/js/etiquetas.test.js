import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { etiquetaCapitulo } from "./format.js";
import { buscar } from "./gastos-tree.js";
import { datosQuesito } from "./quesito.js";
import { filasVista } from "./comparacion.js";

const leer = (r) => JSON.parse(readFileSync(new URL(r, import.meta.url), "utf8"));

test("etiquetaCapitulo escribe «Cap N - nombre»", () => {
  assert.equal(etiquetaCapitulo({ cap: 1, corto: "Personal" }), "Cap 1 - Personal");
  assert.equal(etiquetaCapitulo({ cap: 9, corto: "Préstamos" }), "Cap 9 - Préstamos");
});

test("los quesitos nombran todos los capítulos con su número", () => {
  const { items } = datosQuesito(leer("../data/2026/resumen.json").ingresosPorCapitulo);
  assert.ok(items.length > 5);
  assert.ok(items.every((i) => /^Cap \d - /.test(i.nombre)), items.map((i) => i.nombre).join("|"));
});

test("la búsqueda de gastos indica el capítulo como «Cap N - nombre»", () => {
  const filas = buscar(leer("../data/2026/gastos.json"), "energía eléctrica");
  assert.ok(filas.some((f) => /^Cap 2 - /.test(f.capitulo)), filas.map((f) => f.capitulo).join("|"));
});

test("la comparativa nombra los capítulos con su número", () => {
  const datos = { gastos: leer("../data/2026/gastos.json"), ingresos: leer("../data/2026/ingresos.json"), resumen: leer("../data/2026/resumen.json") };
  for (const vista of ["gastoCapitulos", "ingresoCapitulos"]) {
    const nombres = filasVista(vista, datos, datos, "total").map((f) => f.nombre);
    assert.ok(nombres.length === 9 && nombres.every((n) => /^Cap \d - /.test(n)), nombres.join("|"));
  }
});
