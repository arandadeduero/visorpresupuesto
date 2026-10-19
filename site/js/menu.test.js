// El menú: dos grupos declarados en layout.js, enlaces con ?anio= y aria-current en la sección activa.
import test from "node:test";
import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import { GRUPOS, SECCIONES, menuHtml } from "./layout.js";

const nombres = (g) => g.secciones.map((s) => s[1]);

test("el grupo principal y el de herramientas tienen las secciones pedidas, en orden", () => {
  assert.deepEqual(GRUPOS.map((g) => g.id), ["principal", "herramientas"]);
  assert.deepEqual(nombres(GRUPOS[0]), ["Inicio", "Resumen", "Ingresos", "Gastos", "Inversiones", "Subvenciones", "Deuda"]);
  assert.deepEqual(nombres(GRUPOS[1]), ["Comparar", "Indicadores", "Calculadora", "Guía", "Descargas"]);
});

test("cada página .html del sitio está exactamente en un grupo", () => {
  const paginas = readdirSync(new URL("../", import.meta.url)).filter((f) => f.endsWith(".html")).sort();
  assert.deepEqual(SECCIONES.map((s) => s[2]).sort(), paginas);
});

test("los enlaces llevan ?anio= y solo la sección activa lleva aria-current, sea del grupo que sea", () => {
  for (const activa of ["deuda", "guia"]) {
    const html = menuHtml(activa, 2025);
    assert.equal((html.match(/<a /g) ?? []).length, 12);
    assert.equal((html.match(/\?anio=2025"/g) ?? []).length, 12);
    assert.equal((html.match(/aria-current="page"/g) ?? []).length, 1);
    const { 2: href } = SECCIONES.find((s) => s[0] === activa);
    assert.ok(html.includes(`<a href="${href}?anio=2025" aria-current="page">`));
  }
  assert.ok(!menuHtml("inicio", null).includes("?anio="));
});

test("el grupo secundario lleva la etiqueta «Herramientas»", () => {
  assert.match(menuHtml("inicio", 2026), /menu-herramientas"><span class="menu-etiqueta">Herramientas<\/span>/);
});
