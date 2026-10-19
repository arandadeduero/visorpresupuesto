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

test("por capítulo: el personal no baja de programa", () => {
  const raiz = buildTree(datos, "capitulo");
  assert.ok(Math.abs(suma(raiz) - TOTAL) < 1);
  const personal = raiz.find((n) => n.nombre === "Personal");
  assert.equal(personal.oficial, "Gastos de personal");
  assert.ok(personal.hijos.length > 5);
  assert.ok(personal.hijos.every((p) => p.hijos === null));
  const obras = raiz.find((n) => n.nombre === "Obras e inversiones");
  const seg = obras.hijos.find((n) => n.nombre === "Seguridad");
  assert.deepEqual(seg.hijos.map((p) => p.actual).sort((a, b) => a - b), [45000, 110000]);
});

test("buscar ignora tildes y devuelve programas y partidas", () => {
  const luz = buscar(datos, "ENERGIA electrica");
  assert.ok(luz.length > 0);
  assert.ok(luz.every((r) => /energ[ií]a el[eé]ctrica/i.test(r.nombre)));
  assert.equal(buscar(datos, "   ").length, 0);
  const seg = buscar(datos, "SEGURIDAD");
  assert.ok(seg.some((r) => r.tipo === "programa" && r.nombre === "Seguridad"));
});
