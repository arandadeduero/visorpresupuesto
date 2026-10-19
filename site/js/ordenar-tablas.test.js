import test from "node:test";
import assert from "node:assert/strict";
import { valorCelda, tipoColumna, ordenarFilas } from "./ordenar-tablas.js";

const NBSP = " ";

test("valorCelda entiende importes, porcentajes, signos y millones", () => {
  assert.equal(valorCelda(`1.234.568${NBSP}€`), 1234568);
  assert.equal(valorCelda(`−12,5${NBSP}%`), -12.5);
  assert.equal(valorCelda("+400 %"), 400);
  assert.equal(valorCelda(`2,2${NBSP}M€`), 2200000);
  assert.equal(valorCelda("▲ +9 % frente al año anterior"), 9);
  assert.equal(valorCelda("-12.500 €"), -12500);
  assert.equal(valorCelda("2024"), 2024);
});

test("valorCelda devuelve null cuando no es un número", () => {
  for (const t of ["—", "", "nuevo este año", "Cultura", "Cap 6 - Obras e inversiones", "desaparece", null, undefined]) {
    assert.equal(valorCelda(t), null, String(t));
  }
});

test("tipoColumna es numérica solo si todas las celdas con contenido son números", () => {
  assert.equal(tipoColumna(["10 €", "—", "5 €"]), "numero");
  assert.equal(tipoColumna(["10 €", "nuevo", "5 €"]), "numero"); // «nuevo» y «—» son huecos
  assert.equal(tipoColumna(["Cultura", "Deporte"]), "texto");
  assert.equal(tipoColumna(["Cap 1 - Personal", "Cap 2 - Servicios"]), "texto");
  assert.equal(tipoColumna(["2024", "2025", "2026"]), "numero");
  assert.equal(tipoColumna([]), "texto");
});

test("ordenarFilas ordena texto sin tildes ni mayúsculas, y con números naturales", () => {
  const filas = [["Ávila"], ["zamora"], ["Burgos"], ["Cap 10 - Otros"], ["Cap 9 - Préstamos"]].map((celdas) => ({ celdas }));
  const asc = ordenarFilas(filas, 0, "asc").map((f) => f.celdas[0]);
  assert.deepEqual(asc, ["Ávila", "Burgos", "Cap 9 - Préstamos", "Cap 10 - Otros", "zamora"]);
  assert.deepEqual(ordenarFilas(filas, 0, "desc").map((f) => f.celdas[0]), [...asc].reverse());
});

test("ordenarFilas ordena números y deja siempre al final los huecos", () => {
  const filas = ["5 €", "—", "100 €", "nuevo", "20 €"].map((t, i) => ({ celdas: [`f${i}`, t] }));
  assert.deepEqual(ordenarFilas(filas, 1, "asc").map((f) => f.celdas[1]), ["5 €", "20 €", "100 €", "—", "nuevo"]);
  assert.deepEqual(ordenarFilas(filas, 1, "desc").map((f) => f.celdas[1]), ["100 €", "20 €", "5 €", "—", "nuevo"]);
});

test("ordenarFilas no modifica el original y es estable con empates", () => {
  const filas = [["b", "1"], ["a", "1"], ["c", "1"]].map((celdas) => ({ celdas }));
  const copia = filas.map((f) => f.celdas[0]);
  const orden = ordenarFilas(filas, 1, "asc").map((f) => f.celdas[0]);
  assert.deepEqual(orden, ["b", "a", "c"]);
  assert.deepEqual(filas.map((f) => f.celdas[0]), copia);
});
