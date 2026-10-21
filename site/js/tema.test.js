// Tema claro/oscuro: los tokens de color del CSS (styles.css y escalas.css), resueltos para cada esquema, y el
// contraste de los pares texto/fondo reales de la interfaz (WCAG: 4,5:1 para texto, 3:1 para texto grande y gráficos).
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";

const leer = (ruta) => readFileSync(new URL(ruta, import.meta.url), "utf8");
const sinComentarios = (css) => css.replace(/\/\*[\s\S]*?\*\//g, "");
const CSS = sinComentarios(leer("../css/styles.css"));
const ESCALAS = sinComentarios(leer("../css/escalas.css"));

/** Contenido de las llaves que abren en `desde` (texto justo tras la «{»). */
function bloque(texto, desde) {
  let nivel = 1;
  let i = desde;
  for (; i < texto.length && nivel > 0; i++) nivel += texto[i] === "{" ? 1 : texto[i] === "}" ? -1 : 0;
  return texto.slice(desde, i - 1);
}
const declaraciones = (cuerpo) => new Map([...cuerpo.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)].map((m) => [m[1], m[2].trim()]));

/** Tokens declarados en los bloques `:root` de un texto (sin entrar en @media). */
function tokensRaiz(texto) {
  const mapa = new Map();
  for (const m of texto.matchAll(/(^|\})\s*:root\s*\{/g)) for (const [k, v] of declaraciones(bloque(texto, m.index + m[0].length))) mapa.set(k, v);
  return mapa;
}
const inicioOscuro = CSS.indexOf("@media (prefers-color-scheme: dark)");
assert.ok(inicioOscuro > 0, "falta el bloque @media (prefers-color-scheme: dark)");
const cuerpoOscuro = bloque(CSS, CSS.indexOf("{", inicioOscuro) + 1);
const fueraDelOscuro = CSS.replace(`${CSS.slice(inicioOscuro, CSS.indexOf("{", inicioOscuro))}{${cuerpoOscuro}}`, "");

const CLARO = new Map([...tokensRaiz(fueraDelOscuro), ...tokensRaiz(ESCALAS)]);
const OSCURO = tokensRaiz(cuerpoOscuro);

const tokens = (esquema) => (esquema === "oscuro" ? new Map([...CLARO, ...OSCURO]) : CLARO);

// ---- Resolución de valores ----
function resolver(valor, mapa, pila = []) {
  return valor.replace(/var\((--[\w-]+)\)/g, (_, nombre) => {
    assert.ok(mapa.has(nombre), `variable sin definir: ${nombre}`);
    assert.ok(!pila.includes(nombre), `ciclo de variables: ${[...pila, nombre].join(" -> ")}`);
    return resolver(mapa.get(nombre), mapa, [...pila, nombre]);
  });
}
const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
const aHex = (c) => "#" + c.map((x) => Math.round(x).toString(16).padStart(2, "0")).join("");
const MEZCLA = /^color-mix\(in srgb,\s*(#[0-9a-f]{6})(?:\s+(\d+(?:\.\d+)?)%)?,\s*(#[0-9a-f]{6})(?:\s+(\d+(?:\.\d+)?)%)?\)$/i;
/** Color (#rrggbb) de un token en un esquema; entiende var(), hex y color-mix(in srgb, A, B P%). */
function color(nombre, esquema) {
  const valor = resolver(tokens(esquema).get(nombre) ?? assert.fail(`falta el token ${nombre}`), tokens(esquema)).trim();
  if (/^#[0-9a-f]{6}$/i.test(valor)) return valor.toLowerCase();
  const m = valor.match(MEZCLA);
  assert.ok(m, `${nombre} (${esquema}) no se puede resolver a un color: ${valor}`);
  const [, a, pa, b, pb] = m;
  const peso = pb !== undefined ? Number(pb) / 100 : pa !== undefined ? 1 - Number(pa) / 100 : 0.5;
  return aHex(rgb(a).map((x, i) => x * (1 - peso) + rgb(b)[i] * peso));
}

const luminancia = (hex) => {
  const [r, g, b] = rgb(hex).map((c) => c / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const contraste = (a, b) => {
  const [x, y] = [luminancia(a), luminancia(b)].sort((m, n) => n - m);
  return (x + 0.05) / (y + 0.05);
};

const ESQUEMAS = ["claro", "oscuro"];

test("hay un tema oscuro que solo redefine tokens que existen en el claro", () => {
  assert.match(CSS, /color-scheme:\s*light dark/);
  const nuevos = [...OSCURO.keys()].filter((k) => !CLARO.has(k) && !k.startsWith("--n-") && !/-d$|^--rojo-(cabecera|pastel|aviso)$|^--ambar-aviso$|^--marron-claro-d$/.test(k));
  assert.deepEqual(nuevos, []);
  for (const k of ["--fondo", "--superficie", "--texto", "--texto-suave", "--borde", "--enlace", "--cabecera-fondo", "--aviso-fondo", "--error-fondo", "--foco", "--sombra"]) {
    assert.ok(OSCURO.has(k), `el tema oscuro no redefine ${k}`);
  }
  for (let n = 1; n <= 9; n++) assert.ok(OSCURO.has(`--cap-${n}`), `--cap-${n}`);
  for (let n = 1; n <= 6; n++) assert.ok(OSCURO.has(`--serie-${n}`) && OSCURO.has(`--serie-${n}-texto`), `--serie-${n}`);
});

test("toda variable que se usa está definida y ninguna es circular", () => {
  const usadas = new Set([...(CSS + ESCALAS).matchAll(/var\((--[\w-]+)/g)].map((m) => m[1]));
  for (const nombre of usadas) {
    // --color y --sobre las fija cada clase de color (.serie-N, .cap-N…) y se leen con valor por defecto
    if (nombre === "--color" || nombre === "--sobre") continue;
    assert.ok(CLARO.has(nombre) || OSCURO.has(nombre), `${nombre} se usa pero no se define`);
  }
  for (const esquema of ESQUEMAS) for (const [k] of tokens(esquema)) resolver(`var(${k})`, tokens(esquema));
});

// Pares de texto y fondo que existen de verdad en la interfaz. [texto, fondo, mínimo, dónde]
const PARES = [
  ["--texto", "--fondo", 4.5, "cuerpo"],
  ["--texto", "--superficie", 4.5, "tarjetas, tablas, formularios"],
  ["--texto", "--fondo-suave", 4.5, "cabecera de tablas, ayuda, menú de herramientas"],
  ["--texto-suave", "--fondo", 4.5, "texto secundario"],
  ["--texto-suave", "--superficie", 4.5, "texto secundario en tarjetas"],
  ["--texto-suave", "--fondo-suave", 4.5, "pie, etiquetas del menú, ayuda"],
  ["--enlace", "--fondo", 4.5, "enlaces"],
  ["--enlace", "--superficie", 4.5, "botones, títulos de tarjeta"],
  ["--enlace", "--fondo-suave", 4.5, "enlaces en ayuda y destacado"],
  ["--enlace", "--aviso-fondo", 4.5, "enlaces dentro de avisos"],
  ["--enlace", "--error-fondo", 4.5, "enlaces dentro de errores"],
  ["--texto", "--aviso-fondo", 4.5, "avisos"],
  ["--texto", "--error-fondo", 4.5, "errores"],
  ["--texto-suave", "--aviso-fondo", 4.5, "texto secundario en avisos"],
  ["--var-sube", "--fondo", 4.5, "variación al alza"],
  ["--var-baja", "--fondo", 4.5, "variación a la baja"],
  ["--var-sube", "--fondo-suave", 4.5, "variación en el destacado"],
  ["--var-baja", "--fondo-suave", 4.5, "variación en el destacado"],
  ["--cabecera-texto", "--cabecera-fondo", 4.5, "cabecera y menú"],
  ["--cabecera-activo-texto", "--cabecera-activo-fondo", 4.5, "sección activa del menú"],
  ["--activo-texto", "--activo-fondo", 4.5, "pestaña y herramienta activas"],
  ["--etiqueta-texto", "--etiqueta-fondo", 4.5, "etiquetas «nuevo»"],
  ["--tooltip-texto", "--tooltip-fondo", 4.5, "tooltips de los gráficos"],
  ["--grafico-texto", "--superficie", 4.5, "ejes y leyenda de los gráficos"],
  ["--grafico-texto", "--fondo", 4.5, "ejes y leyenda de los gráficos"],
  // Texto grande o en negrita sobre los bloques de color de la portada y de inversiones (3:1)
  ...[1, 2, 3, 4, 5, 6].map((n) => [`--serie-${n}-texto`, `--serie-${n}`, 3, `bloque ${n} de la portada`]),
  // Componentes e indicadores gráficos (3:1)
  ["--borde-fuerte", "--superficie", 3, "borde de campos y selectores"],
  ["--foco", "--foco-anillo", 3, "foco visible"],
  ["--foco", "--fondo", 3, "foco visible"],
  ["--foco", "--superficie", 3, "foco visible"],
  ["--acento", "--fondo-suave", 3, "relleno de las barras sobre su pista"],
];

for (const esquema of ESQUEMAS) {
  test(`tema ${esquema}: contraste de los pares texto/fondo reales`, () => {
    const fallos = [];
    for (const [t, f, minimo, donde] of PARES) {
      const c = contraste(color(t, esquema), color(f, esquema));
      if (c < minimo) fallos.push(`${t} sobre ${f} (${donde}): ${c.toFixed(2)} < ${minimo}`);
    }
    assert.deepEqual(fallos, []);
  });
}

test("foco visible también sobre la cabecera: en claro lo da el anillo blanco, en oscuro el propio contorno ámbar", () => {
  assert.ok(contraste(color("--foco-anillo", "claro"), color("--cabecera-fondo", "claro")) >= 3);
  assert.ok(contraste(color("--foco", "oscuro"), color("--cabecera-fondo", "oscuro")) >= 3);
});

test("tema oscuro: colores de capítulo, tonos y series se distinguen de la superficie (3:1)", () => {
  const fallos = [];
  for (let n = 1; n <= 9; n++) {
    for (let k = 0; k <= 5; k++) {
      const c = contraste(color(`--cap-${n}-tono-${k}`, "oscuro"), color("--superficie", "oscuro"));
      if (c < 3) fallos.push(`--cap-${n}-tono-${k}: ${c.toFixed(2)}`);
    }
  }
  for (let n = 1; n <= 6; n++) {
    const c = contraste(color(`--serie-${n}`, "oscuro"), color("--superficie", "oscuro"));
    if (c < 3) fallos.push(`--serie-${n}: ${c.toFixed(2)}`);
  }
  assert.deepEqual(fallos, []);
});

test("los tonos de cada capítulo son seis y distintos entre sí en los dos temas", () => {
  for (const esquema of ESQUEMAS) {
    for (let n = 1; n <= 9; n++) {
      const tonos = [0, 1, 2, 3, 4, 5].map((k) => color(`--cap-${n}-tono-${k}`, esquema));
      assert.equal(new Set(tonos).size, 6, `cap ${n} (${esquema}): ${tonos}`);
    }
  }
});

test("los nueve colores de capítulo son distintos en los dos temas", () => {
  for (const esquema of ESQUEMAS) assert.equal(new Set([1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => color(`--cap-${n}`, esquema))).size, 9, esquema);
});

test("la paleta municipal y los colores de capítulo del tema claro no han cambiado", () => {
  const esperado = { "--rojo": "#ce0e2d", "--ambar": "#f5a800", "--marron": "#a4541c", "--azul": "#0083c1", "--azul-claro": "#e9f4f9", "--gris": "#646464", "--gris-oscuro": "#3c3c3c", "--celeste": "#3cb4e5", "--azul-cielo": "#8fc9e6", "--ambar-claro": "#f9d37a" };
  for (const [k, v] of Object.entries(esperado)) assert.equal(color(k, "claro"), v, k);
  assert.equal(color("--enlace", "claro"), "#0070a8");
  assert.deepEqual([1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => color(`--cap-${n}`, "claro")), ["#ce0e2d", "#f5a800", "#646464", "#3cb4e5", "#a4541c", "#0083c1", "#3c3c3c", "#8fc9e6", "#f9d37a"]);
});

test("las dos meta theme-color de cada página coinciden con la cabecera de cada tema", () => {
  const paginas = readdirSync(new URL("../", import.meta.url)).filter((f) => f.endsWith(".html"));
  assert.equal(paginas.length, 13);
  for (const p of paginas) {
    const html = leer(`../${p}`);
    const claro = html.match(/<meta name="theme-color" content="(#[0-9a-f]{6})" media="\(prefers-color-scheme: light\)">/i)?.[1];
    const oscuro = html.match(/<meta name="theme-color" content="(#[0-9a-f]{6})" media="\(prefers-color-scheme: dark\)">/i)?.[1];
    assert.equal(claro?.toLowerCase(), color("--cabecera-fondo", "claro"), `${p}: theme-color claro`);
    assert.equal(oscuro?.toLowerCase(), color("--cabecera-fondo", "oscuro"), `${p}: theme-color oscuro`);
  }
});

test("los gráficos leen sus colores del CSS y se repintan al cambiar el esquema del sistema", () => {
  const charts = leer("./charts.js");
  assert.match(charts, /alCambiarEsquema/);
  assert.match(charts, /Chart\.instances/);
  assert.match(charts, /colorVar\("--grafico-/);
  const colores = leer("./colores.js");
  assert.match(colores, /prefers-color-scheme: dark/);
  assert.match(colores, /addEventListener\("change"/);
});
