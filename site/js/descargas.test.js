// Descargas: un bloque por presupuesto publicado, con sus JSON, su PDF y sus Excel (no solo los del año elegido).
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { descargasHtml } from "./descargas-html.js";

const indice = JSON.parse(readFileSync(new URL("../data/index.json", import.meta.url), "utf8"));

test("hay un bloque por año, del más reciente al más antiguo, con un índice para saltar a cada uno", () => {
  const html = descargasHtml(indice);
  const ids = [...html.matchAll(/<h2 id="presupuesto-(\d{4})"/g)].map((m) => Number(m[1]));
  assert.deepEqual(ids, indice.anios.map((a) => a.anio).reverse());
  for (const { anio } of indice.anios) assert.match(html, new RegExp(`href="#presupuesto-${anio}"`));
});

test("cada año enlaza sus seis JSON y sus documentos originales por su nombre", () => {
  const html = descargasHtml(indice);
  for (const a of indice.anios) {
    for (const f of ["resumen", "ingresos", "gastos", "inversiones", "subvenciones", "deuda"]) assert.ok(html.includes(`data/${a.anio}/${f}.json`), `${a.anio} ${f}`);
    for (const d of a.documentos) assert.ok(html.includes(`/raw/main/${a.anio}/${encodeURIComponent(d)}`), `${a.anio} ${d}`);
  }
});

test("los Excel copiados de un PDF no se presentan como originales", () => {
  const html = descargasHtml({ anios: [{ anio: 2030, tipo: "aprobado", origen: "pdf", documentos: ["A1.xlsx", "Presupuesto 2030.pdf"] }] });
  assert.match(html, /Excel preparados a partir del PDF/);
  assert.doesNotMatch(html, /Excel originales/);
});
