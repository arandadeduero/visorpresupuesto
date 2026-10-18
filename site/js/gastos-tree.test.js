import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { buildTree, buscar } from "./gastos-tree.js";

const datos = JSON.parse(readFileSync(new URL("../data/2026/gastos.json", import.meta.url), "utf8"));
const TOTAL = 64280861.35;
const suma = (nodos) => nodos.reduce((s, n) => s + n.y2026, 0);

test("por programa: las áreas suman el presupuesto y llevan nombre llano", () => {
  const raiz = buildTree(datos, "programa");
  assert.ok(Math.abs(suma(raiz) - TOTAL) < 1);
  assert.ok(raiz.some((n) => n.nombre.startsWith("Servicios básicos")));
  assert.ok(raiz.some((n) => n.nombre === "Deuda"));
});

test("por programa: área → programa → partida, con los importes de Seguridad", () => {
  const area = buildTree(datos, "programa").find((n) => n.nombre.startsWith("Servicios básicos"));
  const seguridad = area.hijos.find((n) => n.nombre === "Seguridad");
  assert.ok(Math.abs(seguridad.y2026 - 2893700) < 1);
  assert.ok(Math.abs(suma(seguridad.hijos) - seguridad.y2026) < 1);
  const edificios = seguridad.hijos.find((n) => n.codigo === "622");
  assert.equal(edificios.y2026, 110000);
  assert.equal(edificios.hijos, null);
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
  assert.deepEqual(seg.hijos.map((p) => p.y2026).sort((a, b) => a - b), [45000, 110000]);
});

test("buscar ignora tildes y devuelve programas y partidas", () => {
  const luz = buscar(datos, "ENERGIA electrica");
  assert.ok(luz.length > 0);
  assert.ok(luz.every((r) => /energ[ií]a el[eé]ctrica/i.test(r.nombre)));
  assert.equal(buscar(datos, "   ").length, 0);
  const seg = buscar(datos, "SEGURIDAD");
  assert.ok(seg.some((r) => r.tipo === "programa" && r.nombre === "Seguridad"));
});
