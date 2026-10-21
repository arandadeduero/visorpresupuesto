// El menú: dos grupos declarados en layout.js, enlaces con ?anio= y aria-current en la sección activa.
import test from "node:test";
import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import { GRUPOS, SECCIONES, RELACIONADOS, menuHtml, relacionadoHtml, pieHtml } from "./layout.js";

const nombres = (g) => g.secciones.map((s) => s[1]);

test("el grupo principal y el de herramientas tienen las secciones pedidas, en orden", () => {
  assert.deepEqual(GRUPOS.map((g) => g.id), ["principal", "herramientas"]);
  assert.deepEqual(nombres(GRUPOS[0]), ["Inicio", "Resumen", "Ingresos", "Gastos", "Inversiones", "Subvenciones", "Deuda"]);
  assert.deepEqual(nombres(GRUPOS[1]), ["Comparar", "Indicadores", "Calculadora", "Guía", "Metodología", "Descargas"]);
});

test("cada página .html del sitio está exactamente en un grupo", () => {
  const paginas = readdirSync(new URL("../", import.meta.url)).filter((f) => f.endsWith(".html")).sort();
  assert.deepEqual(SECCIONES.map((s) => s[2]).sort(), paginas);
});

test("los enlaces llevan ?anio= y solo la sección activa lleva aria-current, sea del grupo que sea", () => {
  for (const activa of ["deuda", "guia"]) {
    const html = menuHtml(activa, 2025);
    assert.equal((html.match(/<a /g) ?? []).length, 13);
    assert.equal((html.match(/\?anio=2025"/g) ?? []).length, 13);
    assert.equal((html.match(/aria-current="page"/g) ?? []).length, 1);
    const { 2: href } = SECCIONES.find((s) => s[0] === activa);
    assert.ok(html.includes(`<a href="${href}?anio=2025" aria-current="page">`));
  }
  assert.ok(menuHtml("inicio", 2025).includes('<a href="./?anio=2025" aria-current="page">Inicio</a>'));
  for (const activa of ["inicio"]) {
    const html = menuHtml(activa, 2025);
    assert.ok(!html.includes("index.html"), "la portada se enlaza como ./");
  }
  assert.ok(!menuHtml("inicio", null).includes("?anio="));
});

test("el grupo secundario lleva la etiqueta «Herramientas»", () => {
  assert.match(menuHtml("inicio", 2026), /menu-herramientas"><span class="menu-etiqueta">Herramientas<\/span>/);
});

test("la portada se enlaza como ./ y sin parámetros cuando no hay año", () => {
  const html = menuHtml("resumen", null);
  assert.ok(html.includes('<a href="./">Inicio</a>'));
  assert.ok(!html.includes("index.html"));
});

test("cada enlace «Relacionado» apunta a una página que existe y no a la propia", () => {
  for (const [pagina, lista] of Object.entries(RELACIONADOS)) {
    assert.ok(SECCIONES.some((s) => s[0] === pagina), pagina);
    assert.ok(lista.length >= 3, `${pagina} con pocos enlaces`);
    for (const [destino, texto] of lista) {
      assert.ok(SECCIONES.some((s) => s[0] === destino), `${pagina} -> ${destino}`);
      assert.notEqual(destino, pagina);
      assert.ok(texto.split(" ").length >= 3, `ancla poco descriptiva: ${texto}`);
    }
    assert.match(relacionadoHtml(pagina, 2025), /<h2 id="titulo-relacionado">Relacionado<\/h2>/);
  }
  assert.equal(relacionadoHtml("guia", 2025), "");
});

test("el pie lleva los enlaces institucionales, la metodología y la fecha de los datos", () => {
  const html = pieHtml("2026-10-21");
  for (const url of ["https://www.arandadeduero.es\"", "https://transparencia.arandadeduero.es\"", "https://github.com/arandadeduero/visorpresupuesto\"", "https://www.arandadeduero.es/politica-privacidad/\"", 'href="metodologia.html"']) {
    assert.ok(html.includes(url), url);
  }
  assert.match(html, /Datos actualizados el 21 de octubre de 2026/);
  assert.ok(!pieHtml(undefined).includes("Datos actualizados"));
});
