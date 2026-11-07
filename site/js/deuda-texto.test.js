import test from "node:test";
import assert from "node:assert/strict";
import { explicaDosPrestamos, avisoPrevisto } from "./deuda-texto.js";

test("explica la diferencia entre 11 M€ y 20,16 M€ sin afirmar más de lo que dicen los datos", () => {
  const t = explicaDosPrestamos(11000000, 20161623.64);
  assert.match(t, /11\.000\.000/);
  assert.match(t, /20\.161\.624/);
  assert.match(t, /9\.161\.624/);
  assert.match(t, /remanentes de tesorería/);
  assert.match(t, /no detallan/);
  assert.doesNotMatch(t, /se debe a que/);
});

test("si el anexo de deuda y las inversiones dan la misma cifra (2027), no habla de dos préstamos ni de una diferencia", () => {
  const t = explicaDosPrestamos(23596825.81, 23596825.81);
  assert.match(t, /misma cifra/);
  assert.doesNotMatch(t, /dos cifras|diferencia/);
});

test("el aviso del préstamo previsto sin fecha concreta (2027) dice el año en lugar de un mes inventado", () => {
  const pv = { importe: 23596825.81, fecha: null, primeraAmortizacion: "2029-12-31", ultimaAmortizacion: "2038-12-31", tipoInteres: "Euribor anual + 0,50%" };
  const html = avisoPrevisto(pv, { titular: { vivaFinConPrevisto: 29255176.75 } }, 23596825.81, 2027);
  assert.match(html, /para 2027, que se empezaría/);
  assert.doesNotMatch(html, /Invalid|NaN|null/);
});
