// Analítica con consentimiento: lógica pura (estado del consentimiento, Do Not Track, cookies) y comprobaciones del código.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import * as cfg from "./analytics-config.js";
import {
  estadoConsentimiento, doNotTrackActivo, guardarValor, nombresCookiesGa, dominiosCookie, urlGtag, claveDeshabilitar, avisoHtml,
} from "./analytics.js";

const DIA = 24 * 60 * 60 * 1000;
const AHORA = Date.UTC(2026, 9, 21, 12, 0, 0);
const raw = (v, t) => JSON.stringify({ v, t });

test("configuración: ID, clave propia, 4 días y política del Ayuntamiento en un solo módulo", () => {
  assert.equal(cfg.GA_ID, "G-BXMC22W46S");
  assert.equal(cfg.CLAVE_CONSENTIMIENTO, "presupuestosAranda:analytics-consent");
  assert.equal(cfg.TTL_RECHAZO_MS, 4 * DIA);
  assert.equal(cfg.URL_POLITICA_PRIVACIDAD, "https://www.arandadeduero.es/politica-privacidad/");
});

test("estadoConsentimiento: sin valor o ilegible hay que preguntar", () => {
  for (const r of [null, undefined, "", "{", "no-json", "null", "42", '"granted"', "[]"]) assert.equal(estadoConsentimiento(r, AHORA), "", String(r));
});

test("estadoConsentimiento: aceptar no caduca", () => {
  assert.equal(estadoConsentimiento(raw("granted", AHORA - 1), AHORA), "granted");
  assert.equal(estadoConsentimiento(raw("granted", AHORA - 400 * DIA), AHORA), "granted");
});

test("estadoConsentimiento: rechazar vale 4 días y luego se vuelve a preguntar", () => {
  assert.equal(estadoConsentimiento(raw("denied", AHORA), AHORA), "denied");
  assert.equal(estadoConsentimiento(raw("denied", AHORA - 4 * DIA + 1), AHORA), "denied");
  assert.equal(estadoConsentimiento(raw("denied", AHORA - 4 * DIA), AHORA), "");
  assert.equal(estadoConsentimiento(raw("denied", AHORA - 30 * DIA), AHORA), "");
});

test("estadoConsentimiento: fecha futura, no numérica o valor desconocido se pregunta", () => {
  assert.equal(estadoConsentimiento(raw("granted", AHORA + 1), AHORA), "");
  assert.equal(estadoConsentimiento(raw("denied", AHORA + DIA), AHORA), "");
  assert.equal(estadoConsentimiento(raw("granted", "ayer"), AHORA), "");
  assert.equal(estadoConsentimiento('{"v":"granted"}', AHORA), "");
  assert.equal(estadoConsentimiento(raw("granted", null), AHORA), "");
  assert.equal(estadoConsentimiento(raw("quizas", AHORA - 1), AHORA), "");
  assert.equal(estadoConsentimiento('{"v":"granted","t":1e999}', AHORA), "");
});

test("doNotTrackActivo: navigator o window a «1» (o «yes», navegadores antiguos)", () => {
  assert.equal(doNotTrackActivo({ doNotTrack: "1" }, {}), true);
  assert.equal(doNotTrackActivo({ doNotTrack: "yes" }, {}), true);
  assert.equal(doNotTrackActivo({}, { doNotTrack: "1" }), true);
  assert.equal(doNotTrackActivo({ doNotTrack: "0" }, {}), false);
  assert.equal(doNotTrackActivo({ doNotTrack: null }, {}), false);
  assert.equal(doNotTrackActivo(undefined, undefined), false);
});

test("claveDeshabilitar y urlGtag usan el ID configurado", () => {
  assert.equal(claveDeshabilitar(), "ga-disable-G-BXMC22W46S");
  assert.equal(urlGtag(), "https://www.googletagmanager.com/gtag/js?id=G-BXMC22W46S");
});

test("nombresCookiesGa solo devuelve las _ga*", () => {
  assert.deepEqual(nombresCookiesGa("_ga=1; _ga_BXMC22W46S=2; otra=3;  _gid=4"), ["_ga", "_ga_BXMC22W46S"]);
  assert.deepEqual(nombresCookiesGa(""), []);
  assert.deepEqual(nombresCookiesGa(undefined), []);
});

test("dominiosCookie: el host y sus dominios superiores, sin el dominio de primer nivel", () => {
  assert.deepEqual(dominiosCookie("presupuestos.arandadeduero.dev"), ["", "; domain=.presupuestos.arandadeduero.dev", "; domain=.arandadeduero.dev"]);
  assert.deepEqual(dominiosCookie("localhost"), [""]);
  assert.deepEqual(dominiosCookie(""), [""]);
});

test("guardarValor: sin localStorage no falla, y con él guarda {v,t} con la clave propia", () => {
  const roto = { setItem() { throw new Error("bloqueado"); } };
  assert.doesNotThrow(() => guardarValor(roto, "granted", AHORA));
  const guardado = {};
  guardarValor({ setItem: (k, v) => { guardado[k] = v; } }, "denied", AHORA);
  assert.deepEqual(JSON.parse(guardado[cfg.CLAVE_CONSENTIMIENTO]), { v: "denied", t: AHORA });
});

test("el aviso: región accesible, texto llano, dos botones y enlace a la política; sin estilos en línea", () => {
  const html = avisoHtml();
  assert.match(html, /role="region"/);
  assert.match(html, /aria-label="[^"]+"/);
  assert.match(html, /data-analytics-accept[^>]*>Aceptar</);
  assert.match(html, /data-analytics-reject[^>]*>Rechazar</);
  assert.ok(html.includes(`href="${cfg.URL_POLITICA_PRIVACIDAD}"`));
  assert.match(html, /No se carga ni se envía nada a Google hasta que pulses “Aceptar”/);
  assert.match(html, /pasados 4 días/);
  assert.ok(!/style=/.test(html));
});

const fuentes = () => {
  const dir = new URL("./", import.meta.url);
  const js = readdirSync(dir).filter((f) => f.endsWith(".js") && !f.endsWith(".test.js"));
  const html = readdirSync(new URL("../", import.meta.url)).filter((f) => f.endsWith(".html"));
  return [...js.map((f) => [f, readFileSync(new URL(f, dir), "utf8")]), ...html.map((f) => [f, readFileSync(new URL(`../${f}`, import.meta.url), "utf8")])];
};

test("el ID, la clave y la política solo están escritos en analytics-config.js", () => {
  for (const [nombre, texto] of fuentes()) {
    if (nombre === "analytics-config.js") continue;
    assert.ok(!texto.includes("BXMC22W46S"), `${nombre} escribe el ID`);
    assert.ok(!texto.includes(":analytics-consent"), `${nombre} escribe la clave de consentimiento`);
    assert.ok(!texto.includes("arandadeduero.es/politica-privacidad"), `${nombre} escribe la URL de la política`);
  }
});

test("solo analytics.js nombra Google, y las páginas cargan la analítica desde layout.js", () => {
  for (const [nombre, texto] of fuentes()) {
    if (nombre === "analytics.js" || nombre.endsWith(".html")) continue; // la CSP de los HTML sí nombra los dominios
    assert.ok(!/googletagmanager|google-analytics/.test(texto), `${nombre} nombra un dominio de Google`);
  }
  assert.match(readFileSync(new URL("./layout.js", import.meta.url), "utf8"), /from "\.\/analytics\.js"/);
});
