import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { buildTree, buscar } from "./gastos-tree.js";

const datos = JSON.parse(readFileSync(new URL("../data/2026/gastos.json", import.meta.url), "utf8"));
const TOTAL = 64280861.35;
const suma = (nodos) => nodos.reduce((s, n) => s + n.actual, 0);

test("por política: las políticas suman el presupuesto y llevan nombre llano", () => {
  const raiz = buildTree(datos, "politica");
  assert.ok(Math.abs(suma(raiz) - TOTAL) < 1);
  for (const nombre of ["Cultura", "Deporte", "Educación", "Bienestar comunitario", "Seguridad y movilidad ciudadana", "Deuda pública"]) {
    assert.ok(raiz.some((n) => n.nombre === nombre), nombre);
  }
  assert.ok(raiz.every((x, i) => i === 0 || raiz[i - 1].actual >= x.actual));
});

test("por política: política → programa → partida, con los importes de Seguridad", () => {
  const politica = buildTree(datos, "politica").find((n) => n.nombre === "Seguridad y movilidad ciudadana");
  const seguridad = politica.hijos.find((n) => n.nombre === "Seguridad");
  assert.ok(Math.abs(seguridad.actual - 2893700) < 1);
  assert.ok(Math.abs(suma(seguridad.hijos) - seguridad.actual) < 1);
  const edificios = seguridad.hijos.find((n) => n.codigo === "622");
  assert.equal(edificios.actual, 110000);
  assert.equal(edificios.hijos, null);
  assert.ok(Math.abs(suma(politica.hijos) - politica.actual) < 1);
});

test("por capítulo: capítulo → artículo → partida, y el personal no baja del artículo", () => {
  const raiz = buildTree(datos, "capitulo");
  assert.ok(Math.abs(suma(raiz) - TOTAL) < 1);
  for (const cap of raiz) assert.ok(Math.abs(suma(cap.hijos) - cap.actual) < 1, cap.nombre);
  const personal = raiz.find((n) => n.nombre === "Personal");
  assert.equal(personal.oficial, "Gastos de personal");
  assert.ok(personal.hijos.some((a) => a.nombre === "Personal funcionario"));
  assert.ok(personal.hijos.every((a) => a.hijos === null));
  const obras = raiz.find((n) => n.nombre === "Obras e inversiones");
  const reposicion = obras.hijos.find((a) => a.codigo === "62");
  assert.equal(reposicion.oficial, "Inversión nueva asociada al funcionamiento operativo de los servicios");
  assert.ok(Math.abs(suma(reposicion.hijos) - reposicion.actual) < 1);
  // el programa pasa a ser el detalle de la partida
  const edificios = reposicion.hijos.find((p) => p.codigo === "622" && p.detalle === "Seguridad");
  assert.equal(edificios.actual, 110000);
  assert.equal(edificios.hijos, null);
});

test("por capítulo: los préstamos que se devuelven son el artículo 91 del capítulo 9", () => {
  const deuda = buildTree(datos, "capitulo").find((n) => n.nombre === "Devolución de préstamos");
  assert.equal(deuda.hijos.length, 1);
  assert.equal(deuda.hijos[0].nombre, "Devolución de préstamos");
  assert.equal(deuda.hijos[0].actual, 535000);
});

test("buscar ignora tildes y devuelve programas y partidas", () => {
  const luz = buscar(datos, "ENERGIA electrica");
  assert.ok(luz.length > 0);
  assert.ok(luz.every((r) => /energ[ií]a el[eé]ctrica/i.test(r.nombre)));
  assert.equal(buscar(datos, "   ").length, 0);
  const seg = buscar(datos, "SEGURIDAD");
  assert.ok(seg.some((r) => r.tipo === "programa" && r.nombre === "Seguridad"));
});
