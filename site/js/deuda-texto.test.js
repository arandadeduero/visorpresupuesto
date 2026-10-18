import test from "node:test";
import assert from "node:assert/strict";
import { explicaDosPrestamos } from "./deuda-texto.js";

test("explica la diferencia entre 11 M€ y 20,16 M€ sin afirmar más de lo que dicen los datos", () => {
  const t = explicaDosPrestamos(11000000, 20161623.64);
  assert.match(t, /11\.000\.000/);
  assert.match(t, /20\.161\.624/);
  assert.match(t, /9\.161\.624/);
  assert.match(t, /remanentes de tesorería/);
  assert.match(t, /no detallan/);
  assert.doesNotMatch(t, /se debe a que/);
});
