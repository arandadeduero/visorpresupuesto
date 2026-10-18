import test from "node:test";
import assert from "node:assert/strict";
import { formatEuros, formatVariation, normalize, matches, sumBy } from "./format.js";

const NBSP = " ";

test("formatEuros agrupa miles y redondea", () => {
  assert.equal(formatEuros(1234567.8), `1.234.568${NBSP}€`);
  assert.equal(formatEuros(950), `950${NBSP}€`);
});

test("formatEuros sin dato muestra una raya", () => {
  assert.equal(formatEuros(null), "—");
  assert.equal(formatEuros(undefined), "—");
});

test("formatEuros compacto usa millones", () => {
  assert.equal(formatEuros(11000000, { compact: true }), `11${NBSP}M€`);
  assert.equal(formatEuros(2181340.81, { compact: true }), `2,2${NBSP}M€`);
  assert.equal(formatEuros(45000, { compact: true }), `45.000${NBSP}€`);
});

test("formatVariation sube, baja y se mantiene", () => {
  const up = formatVariation(110, 100);
  assert.equal(up.dir, "up");
  assert.ok(up.text.includes("10 %"), up.text);
  assert.equal(formatVariation(90, 100).dir, "down");
  assert.equal(formatVariation(100, 100).dir, "flat");
});

test("formatVariation nunca produce NaN ni Infinity", () => {
  assert.equal(formatVariation(50, 0).dir, "new");
  assert.equal(formatVariation(50, null).dir, "new");
  assert.equal(formatVariation(null, null).dir, "na");
  assert.equal(formatVariation(0, 0).dir, "flat");
  for (const [a, b] of [[50, 0], [null, null], [0, 0], [0, 100], [undefined, 5]]) {
    assert.doesNotMatch(formatVariation(a, b).text, /NaN|Infinity/);
  }
});

test("matches ignora tildes y mayúsculas", () => {
  assert.equal(matches("Asoc. Cáritas", "CARITAS"), true);
  assert.equal(matches("Cruz Roja", "caritas"), false);
  assert.equal(normalize("Ñandú ÁÉÍ"), "ñandu aei");
});

test("sumBy suma ignorando valores vacíos", () => {
  assert.equal(sumBy([{ v: 1 }, { v: null }, { v: 2.5 }], (x) => x.v), 3.5);
});
