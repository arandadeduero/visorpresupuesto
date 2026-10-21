// URLs de las páginas: con build (data-raiz en <html>) cada año tiene su carpeta; sin build se sigue usando «?anio=».
import test from "node:test";
import assert from "node:assert/strict";

const { urlPagina, enBuild, anioDeLaUrl, esRaiz, destinoAntiguo, urlCambioDeAnio, PAGINAS_SIN_ANIO } = await import("./rutas.js");

/** Ejecuta `fn` como si <html> llevara estos atributos data-* (null: página sin build). */
function con(dataset, fn) {
  const antes = globalThis.document;
  globalThis.document = dataset ? { documentElement: { dataset } } : undefined;
  try {
    return fn();
  } finally {
    globalThis.document = antes;
  }
}
const ANIO = { raiz: "../", anio: "2025", ultimo: "2026" };
const RAIZ = { raiz: "", ultimo: "2026" };
const indice = { ultimo: 2026, anios: [{ anio: 2024 }, { anio: 2025 }, { anio: 2026 }] };

test("sin build: enlaces con ?anio= y la portada como ./", () => {
  con(null, () => {
    assert.equal(enBuild(), false);
    assert.equal(urlPagina("gastos", 2025), "gastos.html?anio=2025");
    assert.equal(urlPagina("gastos"), "gastos.html");
    assert.equal(urlPagina("inicio", 2025), "./?anio=2025");
    assert.equal(urlPagina("inicio"), "./");
    assert.equal(urlPagina("guia", 2025), "guia.html?anio=2025");
    assert.equal(anioDeLaUrl(), null);
  });
});

test("página de un año (/2025/): los enlaces van a la carpeta del año y las páginas sin año a la raíz", () => {
  con(ANIO, () => {
    assert.equal(enBuild(), true);
    assert.equal(anioDeLaUrl(), 2025);
    assert.equal(esRaiz(), false);
    assert.equal(urlPagina("gastos", 2025), "../2025/gastos.html");
    assert.equal(urlPagina("gastos", 2024), "../2024/gastos.html");
    assert.equal(urlPagina("inicio", 2025), "../2025/");
    assert.equal(urlPagina("inicio", 2026), "../", "el último año tiene su portada en la raíz");
    assert.equal(urlPagina("gastos", 2026), "../2026/gastos.html");
    for (const id of PAGINAS_SIN_ANIO) assert.equal(urlPagina(id, 2025), `../${id}.html`);
  });
});

test("raíz (alias del último año, portada y páginas sin año): rutas sin ../", () => {
  con(RAIZ, () => {
    assert.equal(anioDeLaUrl(), null);
    assert.equal(esRaiz(), true);
    assert.equal(urlPagina("gastos", 2026), "2026/gastos.html");
    assert.equal(urlPagina("gastos"), "2026/gastos.html", "sin año, el último");
    assert.equal(urlPagina("gastos", 2025), "2025/gastos.html");
    assert.equal(urlPagina("inicio", 2026), "./");
    assert.equal(urlPagina("inicio", 2025), "2025/");
    assert.equal(urlPagina("comparar", 2025), "comparar.html");
  });
});

test("?anio= antiguo en una página de la raíz: redirige a la carpeta del año y conserva el resto", () => {
  con(RAIZ, () => {
    assert.equal(destinoAntiguo("gastos", indice, "?anio=2025"), "2025/gastos.html");
    assert.equal(destinoAntiguo("gastos", indice, "?anio=2025&modo=x", "#abrir"), "2025/gastos.html?modo=x#abrir");
    assert.equal(destinoAntiguo("inicio", indice, "?anio=2024"), "2024/");
    assert.equal(destinoAntiguo("gastos", indice, "?anio=2026"), null, "es el último: ya estás en él");
    assert.equal(destinoAntiguo("gastos", indice, "?anio=1999"), null, "año que no existe: lo avisa la página");
    assert.equal(destinoAntiguo("gastos", indice, ""), null);
    assert.equal(destinoAntiguo("comparar", indice, "?anio=2025&a=2024&b=2025"), null, "comparar no tiene carpeta de año");
  });
  con(ANIO, () => assert.equal(destinoAntiguo("gastos", indice, "?anio=2024"), null, "en /2025/ manda la ruta"));
  con(null, () => assert.equal(destinoAntiguo("gastos", indice, "?anio=2025"), null, "sin build no hay carpetas"));
});

test("el selector de año navega a la misma página del otro año (o a ?anio= sin build)", () => {
  con(ANIO, () => {
    assert.equal(urlCambioDeAnio("gastos", 2024, "?x=1"), "../2024/gastos.html");
    assert.equal(urlCambioDeAnio("gastos", 2026, ""), "../2026/gastos.html");
    assert.equal(urlCambioDeAnio("inicio", 2026, ""), "../");
    assert.equal(urlCambioDeAnio("guia", 2024, ""), "../2024/", "las páginas sin año llevan a la portada de ese año");
  });
  con(RAIZ, () => assert.equal(urlCambioDeAnio("gastos", 2025, ""), "2025/gastos.html"));
  con(null, () => {
    assert.equal(urlCambioDeAnio("gastos", 2025, "?anio=2024"), "?anio=2025");
    assert.equal(urlCambioDeAnio("comparar", 2025, "?a=2024&b=2026"), "?a=2024&b=2026&anio=2025");
  });
});
