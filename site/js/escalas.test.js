import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { claseAncho, claseCrece } from "./escalas.js";

test("claseAncho redondea al porcentaje y nunca deja a cero algo que existe", () => {
  assert.equal(claseAncho(50, 100), "ancho-50");
  assert.equal(claseAncho(100, 100), "ancho-100");
  assert.equal(claseAncho(1, 1000), "ancho-1"); // 0,1 % se ve como 1 %
  assert.equal(claseAncho(0, 100), "ancho-0");
  assert.equal(claseAncho(5, 0), "ancho-0");
  assert.equal(claseAncho(-3, 10), "ancho-0");
  assert.equal(claseAncho(250, 100), "ancho-100");
  assert.equal(claseAncho(Number.NaN, 100), "ancho-0");
});

test("claseCrece da proporciones de 1 a 100", () => {
  assert.equal(claseCrece(30, 100), "crece-30");
  assert.equal(claseCrece(1, 10000), "crece-1");
  assert.equal(claseCrece(0, 100), "crece-1");
  assert.equal(claseCrece(5, 0), "crece-1");
  assert.equal(claseCrece(100, 100), "crece-100");
});

test("todas las clases que se pueden devolver existen en escalas.css", () => {
  const css = readFileSync(new URL("../css/escalas.css", import.meta.url), "utf8");
  for (let n = 0; n <= 100; n++) assert.ok(css.includes(`.ancho-${n} {`), `.ancho-${n}`);
  for (let n = 1; n <= 100; n++) assert.ok(css.includes(`.crece-${n} {`), `.crece-${n}`);
});
