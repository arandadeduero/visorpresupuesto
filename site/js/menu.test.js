// El menú: dos grupos declarados en layout.js, enlaces con ?anio= y aria-current en la sección activa.
import test from "node:test";
import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import { GRUPOS, SECCIONES, RELACIONADOS, menuHtml, relacionadoHtml, pieHtml, aniosHtml, marcoHtml, tarjetasHtml } from "./layout.js";

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

test("sin build, los enlaces llevan ?anio= y solo la sección activa lleva aria-current, sea del grupo que sea", () => {
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

// ---- Con build: carpetas por año (data-raiz en <html>) ----
function conBuild(dataset, fn) {
  const antes = globalThis.document;
  globalThis.document = { documentElement: { dataset } };
  try {
    return fn();
  } finally {
    globalThis.document = antes;
  }
}
const indice = { ultimo: 2026, anios: [{ anio: 2024, tipo: "inicial" }, { anio: 2025, tipo: "inicial" }, { anio: 2026, tipo: "inicial" }] };

test("con build, el menú de /2025/ lleva a la carpeta del año y las páginas sin año a la raíz, sin ?anio=", () => {
  conBuild({ raiz: "../", anio: "2025", ultimo: "2026" }, () => {
    const html = menuHtml("gastos", 2025);
    assert.ok(html.includes('<a href="../2025/gastos.html" aria-current="page">Gastos</a>'));
    assert.ok(html.includes('<a href="../2025/">Inicio</a>'));
    assert.ok(html.includes('<a href="../guia.html">Guía</a>') && html.includes('<a href="../comparar.html">Comparar</a>'));
    assert.ok(!html.includes("?anio="));
    assert.ok(relacionadoHtml("gastos", 2025).includes('href="../2025/ingresos.html"'));
    assert.ok(relacionadoHtml("gastos", 2025).includes('href="../guia.html"'));
    assert.ok(tarjetasHtml(2025).includes('href="../2025/deuda.html"'));
    assert.ok(pieHtml("2026-10-21", 2025).includes('href="../metodologia.html"'));
  });
});

test("con build, la raíz enlaza el último año sin repetir su carpeta en la portada", () => {
  conBuild({ raiz: "", ultimo: "2026" }, () => {
    const html = menuHtml("inicio", 2026);
    assert.ok(html.includes('<a href="./" aria-current="page">Inicio</a>'));
    assert.ok(html.includes('<a href="2026/gastos.html">Gastos</a>'));
    const marco = marcoHtml({ activa: "inicio", anio: 2026, indice, escudo: "img/escudo.png", actualizado: "2026-10-21" });
    assert.ok(marco.includes('<a class="marca" href="./">'));
    assert.ok(marco.includes('<option value="2026" selected>'));
  });
});

test("«Otros años»: la misma página en los demás años, con anclas descriptivas; sin nada en las páginas sin año", () => {
  conBuild({ raiz: "../", anio: "2025", ultimo: "2026" }, () => {
    const html = aniosHtml("gastos", 2025, indice);
    assert.match(html, /Otros años: <a href="\.\.\/2024\/gastos\.html">Gastos de 2024<\/a> · <a href="\.\.\/2026\/gastos\.html">Gastos de 2026<\/a>/);
    assert.ok(!html.includes("2025/"));
    assert.ok(aniosHtml("inicio", 2025, indice).includes('href="../"'), "la portada del último año es la raíz");
    for (const id of ["comparar", "guia", "metodologia", "descargas"]) assert.equal(aniosHtml(id, 2025, indice), "");
  });
});

test("en la portada de la raíz, un bloque «Presupuestos por año» con un enlace a cada año", () => {
  conBuild({ raiz: "", ultimo: "2026" }, () => {
    const html = aniosHtml("inicio", 2026, indice);
    assert.match(html, /<h2 id="titulo-anios">Presupuestos por año<\/h2>/);
    for (const a of [2024, 2025, 2026]) assert.ok(html.includes(`Presupuesto de ${a}: en qué se gasta</a>`), a);
    assert.ok(html.includes('href="2025/"') && html.includes('href="2024/"'));
    assert.ok(!html.includes('href="2026/"'), "la portada del último año es la propia raíz");
    assert.ok(html.includes('href="2026/gastos.html"'));
  });
});

test("sin build, «Otros años» enlaza con ?anio=", () => {
  const html = aniosHtml("deuda", 2026, indice);
  assert.ok(html.includes('href="deuda.html?anio=2024"') && html.includes('href="deuda.html?anio=2025"'));
});
