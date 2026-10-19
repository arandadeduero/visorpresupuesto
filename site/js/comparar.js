// Página «Comparar»: elige dos presupuestos y muestra qué ha cambiado (barras pareadas, tabla, frases, indicadores y evolución).
import { runPage, esc } from "./layout.js";
import { getIndex, loadData } from "./data.js";
import { formatEuros } from "./format.js";
import { barChart } from "./charts.js";
import { tablaHtml } from "./ui.js";
import { elegirPareja, filasVista, ordenar, frase, titular, serieEvolucion, filasIndicadores } from "./comparacion.js";

const VISTAS = [
  { id: "politicas", texto: "Gastos por política", verbo: "gastar", que: "gastos" },
  { id: "gastoCapitulos", texto: "Gastos por capítulo", verbo: "gastar", que: "gastos" },
  { id: "ingresoCapitulos", texto: "Ingresos por capítulo", verbo: "ingresar", que: "ingresos" },
  { id: "indicadores", texto: "Indicadores" },
];
const ORDENES = [
  ["importe", "Mayor importe"],
  ["sube", "Lo que más sube (€)"],
  ["baja", "Lo que más baja (€)"],
  ["pct", "Mayor cambio en %"],
  ["nombre", "Nombre (A-Z)"],
];
const COLOR_A = "#0083c1";
const COLOR_B = "#f5a800";
const COLOR_OTRO = "#646464";

const num = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 1 });
const euros = (v, modo) => (v === null || v === undefined ? "—" : modo === "habitante" ? formatEuros(v) : formatEuros(v, { compact: false }));
const conSigno = (d, modo) => (d === null ? "—" : `${d > 0 ? "+" : d < 0 ? "−" : ""}${euros(Math.abs(d), modo)}`);
const pctTxt = (p) => (p === null ? "" : `${p > 0 ? "+" : p < 0 ? "−" : ""}${num.format(Math.abs(p))} %`);

function difHtml(f, modo) {
  if (f.estado === "nuevo") return `<span class="var-up">● Nuevo: ${conSigno(f.delta, modo)}</span>`;
  if (f.estado === "desaparece") return `<span class="var-down">● Desaparece: ${conSigno(f.delta, modo)}</span>`;
  if (f.estado === "igual") return `<span>＝ Sin cambios</span>`;
  const clase = f.estado === "sube" ? "var-up" : "var-down";
  return `<span class="${clase}">${f.estado === "sube" ? "▲" : "▼"} ${conSigno(f.delta, modo)}${f.pct === null ? "" : ` (${pctTxt(f.pct)})`}</span>`;
}

const fmtInd = (v, tipo) => (v === null ? "—" : tipo === "pct" ? `${num.format(v)} %` : formatEuros(v, { compact: Math.abs(v) >= 1e6 }));
const fmtIndDelta = (d, tipo) => (d === null ? "—" : tipo === "pct" ? `${d > 0 ? "+" : d < 0 ? "−" : ""}${num.format(Math.abs(d))} puntos` : `${d > 0 ? "+" : d < 0 ? "−" : ""}${formatEuros(Math.abs(d), { compact: Math.abs(d) >= 1e6 })}`);

runPage("comparar", async ({ main }) => {
  document.querySelector(".anio")?.remove(); // aquí se eligen dos años, no uno
  const indice = await getIndex();
  const anios = indice.anios.map((a) => a.anio);
  const cargados = await Promise.all(
    anios.map(async (anio) => {
      const [gastos, ingresos, resumen, deuda] = await Promise.all(["gastos", "ingresos", "resumen", "deuda"].map((n) => loadData(anio, n)));
      return { anio, gastos, ingresos, resumen, deuda };
    }),
  );
  const porAnio = new Map(cargados.map((d) => [d.anio, d]));

  const url = new URLSearchParams(location.search);
  const pareja = elegirPareja(anios, url.get("a"), url.get("b"));
  const estado = {
    a: pareja.a,
    b: pareja.b,
    vista: VISTAS.some((v) => v.id === url.get("vista")) ? url.get("vista") : "politicas",
    modo: url.get("modo") === "habitante" ? "habitante" : "total",
    orden: ORDENES.some((o) => o[0] === url.get("orden")) ? url.get("orden") : "importe",
    clave: url.get("clave"),
  };
  let grafico = null;

  function guardarUrl() {
    const p = new URLSearchParams({ a: estado.a, b: estado.b, vista: estado.vista, modo: estado.modo, orden: estado.orden });
    if (estado.clave) p.set("clave", estado.clave);
    history.replaceState(null, "", `?${p}`);
  }

  function pinta() {
    if (grafico) {
      grafico.destroy();
      grafico = null;
    }
    guardarUrl();
    const { a, b, vista, modo } = estado;
    document.title = `Comparar ${a} y ${b} · Presupuestos de Aranda de Duero`;
    if (b === null) {
      main.innerHTML = `<h1>Comparar presupuestos</h1><div class="aviso"><p>Solo hay un presupuesto publicado, así que todavía no se puede comparar.</p></div>`;
      return;
    }
    const dA = porAnio.get(a);
    const dB = porAnio.get(b);
    const conf = VISTAS.find((v) => v.id === vista);
    const opcionesAnio = (sel, otro) => anios.map((y) => `<option value="${y}"${y === sel ? " selected" : ""}${y === otro ? " disabled" : ""}>${y}</option>`).join("");
    const tg = titular(dA, dB, "gastos", modo);
    const ti = titular(dA, dB, "ingresos", modo);
    const tarjeta = (titulo, t) => `<section class="card"><h2 class="card-titulo">${titulo}</h2>
      <p class="comp-cifras"><span><i class="punto" style="background:${COLOR_A}"></i>${a}: <strong>${euros(t.a, modo)}</strong></span><span><i class="punto" style="background:${COLOR_B}"></i>${b}: <strong>${euros(t.b, modo)}</strong></span></p>
      <p class="muted">${t.delta === null ? "" : `${t.delta > 0 ? "Sube" : t.delta < 0 ? "Baja" : "Igual"} ${conSigno(t.delta, modo)}${t.pct === null ? "" : ` (${pctTxt(t.pct)})`} de ${a} a ${b}`}</p></section>`;

    const pestanas = VISTAS.map((v) => `<button type="button" data-vista="${v.id}" aria-pressed="${v.id === vista}">${v.texto}</button>`).join("");
    const modos = [["total", "Total"], ["habitante", "Por habitante"]]
      .map(([id, t]) => `<button type="button" data-modo="${id}" aria-pressed="${id === modo}">${t}</button>`)
      .join("");

    let cuerpo = "";
    if (vista === "indicadores") {
      const f = filasIndicadores(dA, dB);
      cuerpo = `<h2>Indicadores de ${a} y ${b}</h2>
        <p class="muted">Calculados con las cifras de cada presupuesto inicial (más explicaciones en la <a href="indicadores.html?anio=${b}">página de indicadores</a>). Si un año no trae el dato, aparece una raya. El nivel de endeudamiento y el ahorro neto son estimaciones con el presupuesto inicial: la ley los calcula con la liquidación del año anterior.</p>
        ${tablaHtml(
          [{ texto: "Indicador" }, { texto: `${a}`, num: true }, { texto: `${b}`, num: true }, { texto: "Cambio", num: true }],
          f.map((x) => `<tr><td>${esc(x.etiqueta)}</td><td class="num">${fmtInd(x.a, x.tipo)}</td><td class="num">${fmtInd(x.b, x.tipo)}</td><td class="num">${fmtIndDelta(x.delta, x.tipo)}</td></tr>`),
        )}`;
    } else {
      const filas = ordenar(filasVista(vista, dA, dB, modo), estado.orden);
      const max = Math.max(0, ...filas.map((f) => Math.max(f.a ?? 0, f.b ?? 0)));
      const ancho = (v) => (v && max > 0 ? Math.min(100, (v / max) * 100).toFixed(1) : "0");
      const claves = filas.map((f) => f.clave);
      if (!claves.includes(estado.clave)) estado.clave = ordenar(filas, "importe")[0]?.clave ?? null;
      const barra = (anio, v, color) => `<div class="par-barra"><span class="par-anio">${anio}</span><span class="pista" aria-hidden="true"><span class="relleno" style="width:${ancho(v)}%;background:${color}"></span></span><span class="par-imp">${euros(v, modo)}</span></div>`;
      const destacadas = [...filas].filter((f) => f.estado !== "igual").sort((x, y) => Math.abs(y.delta) - Math.abs(x.delta)).slice(0, 3);
      const unidad = modo === "habitante" ? " Los importes son euros por habitante, con la población de cada año." : "";
      cuerpo = `
        <h2>${conf.texto}: ${a} frente a ${b}</h2>
        ${destacadas.length ? `<h3>Lo más destacado</h3><ul class="frases">${destacadas.map((f) => `<li>${esc(frase(f, a, b, { verbo: conf.verbo, modo }))}</li>`).join("")}</ul>` : ""}
        <div class="comp-controles"><label>Ordenar por <select id="orden">${ORDENES.map(([id, t]) => `<option value="${id}"${id === estado.orden ? " selected" : ""}>${t}</option>`).join("")}</select></label>
          <span class="leyenda"><span><i class="punto" style="background:${COLOR_A}"></i>${a}</span><span><i class="punto" style="background:${COLOR_B}"></i>${b}</span></span></div>
        <ul class="barras pares">${filas
          .map(
            (f) => `<li class="par"><div class="par-cab"><button type="button" class="par-nombre" data-clave="${esc(f.clave)}" title="Ver su evolución en todos los años">${esc(f.nombre)}</button>${f.estado === "nuevo" ? '<span class="etiqueta">nuevo</span>' : f.estado === "desaparece" ? '<span class="etiqueta">desaparece</span>' : ""}</div>
            ${barra(a, f.a, COLOR_A)}${barra(b, f.b, COLOR_B)}<div class="par-dif">${difHtml(f, modo)}</div></li>`,
          )
          .join("")}</ul>
        <h3>Como tabla</h3>
        ${tablaHtml(
          [{ texto: "Concepto" }, { texto: `${a}`, num: true }, { texto: `${b}`, num: true }, { texto: "Diferencia", num: true }, { texto: "%", num: true }],
          filas.map((f) => `<tr><td>${esc(f.nombre)}${f.estado === "nuevo" ? " (nuevo)" : f.estado === "desaparece" ? " (desaparece)" : ""}</td><td class="num">${euros(f.a, modo)}</td><td class="num">${euros(f.b, modo)}</td><td class="num">${conSigno(f.delta, modo)}</td><td class="num">${f.pct === null ? "—" : pctTxt(f.pct)}</td></tr>`),
        )}
        <section id="evolucion"><h2>Evolución en todos los años</h2>
          <label>Ver la evolución de <select id="clave">${ordenar(filas, "nombre").map((f) => `<option value="${esc(f.clave)}"${f.clave === estado.clave ? " selected" : ""}>${esc(f.nombre)}</option>`).join("")}</select></label>
          <p class="leyenda"><span><i class="punto" style="background:${COLOR_A}"></i>${a}</span><span><i class="punto" style="background:${COLOR_B}"></i>${b}</span><span><i class="punto" style="background:${COLOR_OTRO}"></i>Otros años</span></p>
          <div class="grafico"><canvas id="evol" role="img" aria-label="Evolución del importe en todos los años"></canvas></div>
          <div id="evol-tabla"></div>
          <p class="muted">${unidad}</p>
        </section>`;
    }

    main.innerHTML = `
      <h1>Comparar presupuestos</h1>
      <p class="lead">Elige dos años y mira qué ha cambiado entre ellos.</p>
      <div class="comp-selectores">
        <label>Presupuesto de <select id="sel-a">${opcionesAnio(a, b)}</select></label>
        <label>frente al de <select id="sel-b">${opcionesAnio(b, a)}</select></label>
      </div>
      <div class="cards">${tarjeta("Gastos previstos", tg)}${tarjeta("Ingresos previstos", ti)}</div>
      <div class="ayuda"><p>Son <strong>presupuestos iniciales</strong>, es decir, previsiones y no gasto ya realizado. Los importes son <strong>euros de cada año</strong>, sin descontar la inflación: con la subida de precios, el mismo dinero compra menos cada año.</p></div>
      <div class="pestanas" role="group" aria-label="Qué comparar">${pestanas}</div>
      ${vista === "indicadores" ? "" : `<div class="pestanas comp-modo" role="group" aria-label="Cómo mostrar los importes">${modos}</div>`}
      ${cuerpo}`;

    const el = (id) => main.querySelector(id);
    el("#sel-a").addEventListener("change", (e) => cambiaPareja(e.target.value, estado.b));
    el("#sel-b").addEventListener("change", (e) => cambiaPareja(estado.a, e.target.value));
    main.querySelectorAll("[data-vista]").forEach((x) => x.addEventListener("click", () => { estado.vista = x.dataset.vista; estado.clave = null; pinta(); }));
    main.querySelectorAll("[data-modo]").forEach((x) => x.addEventListener("click", () => { estado.modo = x.dataset.modo; pinta(); }));
    if (vista === "indicadores") return;
    el("#orden").addEventListener("change", (e) => { estado.orden = e.target.value; pinta(); });
    el("#clave").addEventListener("change", (e) => { estado.clave = e.target.value; pinta(); });
    main.querySelectorAll("[data-clave]").forEach((x) => x.addEventListener("click", () => {
      estado.clave = x.dataset.clave;
      pinta();
      el("#evolucion").scrollIntoView({ behavior: "smooth" });
    }));
    pintaEvolucion();
  }

  function cambiaPareja(a, b) {
    const p = elegirPareja(anios, a, b);
    estado.a = p.a;
    estado.b = p.b;
    pinta();
  }

  function pintaEvolucion() {
    const serie = serieEvolucion(cargados, estado.vista, estado.clave, estado.modo);
    const color = (anio) => (anio === estado.a ? COLOR_A : anio === estado.b ? COLOR_B : COLOR_OTRO);
    const canvas = main.querySelector("#evol");
    if (typeof Chart !== "undefined") {
      grafico = barChart(canvas, {
        labels: serie.map((p) => String(p.anio)),
        datasets: [{ label: estado.modo === "habitante" ? "Euros por habitante" : "Euros", data: serie.map((p) => p.valor ?? 0), backgroundColor: serie.map((p) => color(p.anio)), borderRadius: 4 }],
      });
    }
    main.querySelector("#evol-tabla").innerHTML = tablaHtml(
      [{ texto: "Año" }, { texto: estado.modo === "habitante" ? "Euros por habitante" : "Importe", num: true }, { texto: "Cambio sobre el año anterior", num: true }],
      serie.map((p, i) => {
        const antes = i > 0 ? serie[i - 1].valor : null;
        const d = p.valor !== null && antes !== null ? p.valor - antes : null;
        const pc = d !== null && antes > 0 ? (d / antes) * 100 : null;
        return `<tr><td>${p.anio}</td><td class="num">${p.valor === null ? "no existe" : euros(p.valor, estado.modo)}</td><td class="num">${d === null ? "—" : `${conSigno(d, estado.modo)}${pc === null ? "" : ` (${pctTxt(pc)})`}`}</td></tr>`;
      }),
    );
  }

  pinta();
});
