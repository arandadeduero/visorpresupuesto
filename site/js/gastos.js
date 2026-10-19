import { runPage, esc } from "./layout.js";
import { formatEuros } from "./format.js";
import { buildTree, buscar } from "./gastos-tree.js";
import { filaHtml, variacionHtml, tablaHtml, porHabHtml } from "./ui.js";
import { pintaQuesito } from "./quesito.js";

runPage("gastos", async ({ anio, main, load }) => {
  const [datos, resumen] = await Promise.all([load("gastos"), load("resumen")]);
  const habitantes = resumen.habitantes;
  const total = datos.capitulos.reduce((s, c) => s + c.actual, 0);
  let modo = "politica";
  let nodos = new Map();

  main.innerHTML = `
    <h1>¿En qué se gasta el dinero? <span class="muted">${anio}</span></h1>
    <p class="lead">Total previsto: <strong>${formatEuros(total)}</strong>. Unos <strong>${porHabHtml(total, habitantes)}</strong>. Pulsa en cada línea para ver su detalle.</p>
    <p class="muted">Importe por habitante = gasto del Ayuntamiento dividido entre ${habitantes.toLocaleString("es-ES")} habitantes (${esc(resumen.fuentePoblacion)}). No es lo que paga cada vecino.</p>
    <div id="quesito"></div>
    <div class="controles">
      <div class="pestanas" role="group" aria-label="Cómo agrupar los gastos">
        <button type="button" data-modo="politica" aria-pressed="true">¿En qué se gasta?</button>
        <button type="button" data-modo="capitulo" aria-pressed="false">¿Qué tipo de gasto es?</button>
      </div>
    </div>
    <p class="muted" id="explica-modo"></p>
    <p><label>Buscar un gasto <input type="search" id="buscar" placeholder="Por ejemplo: energía, parques, cultura…" autocomplete="off"></label></p>
    <div id="arbol"></div>
    <div id="resultados" hidden></div>
    <div class="ayuda"><strong>Sobre el personal:</strong> los sueldos y cotizaciones se muestran agrupados por programa (en «¿En qué se gasta?») o por tipo de personal (en «¿Qué tipo de gasto es?»), sin detalle por categoría. El resto de gastos llega hasta la partida concreta (en «¿Qué tipo de gasto es?», con el programa al que pertenece).</div>`;

  pintaQuesito(main.querySelector("#quesito"), datos.capitulos, "Gastos por tipo de gasto", datos.articulos);
  const arbol = main.querySelector("#arbol");
  const resultados = main.querySelector("#resultados");

  const indexar = (lista) => lista.forEach((n) => { nodos.set(n.id, n); if (n.hijos) indexar(n.hijos); });

  function lista(hijos) {
    const max = Math.max(...hijos.map((n) => n.actual), 1);
    return `<ul class="barras">${hijos.map((n) => `<li>${filaHtml({
      id: n.id,
      nombre: n.nombre,
      title: n.oficial ? `Nombre oficial: ${n.oficial}` : undefined,
      importe: n.actual,
      max,
      clicable: Boolean(n.hijos),
      extra: [n.detalle ? esc(n.detalle) : "", `${((n.actual / total) * 100).toLocaleString("es-ES", { maximumFractionDigits: 1 })} % del total`, porHabHtml(n.actual, habitantes), n.anterior == null ? "" : variacionHtml(n.actual, n.anterior)].filter(Boolean).join(" · "),
    })}<div class="hijos" hidden></div></li>`).join("")}</ul>`;
  }

  const EXPLICA = {
    politica: "Agrupa los gastos por la finalidad a la que se destinan (cultura, deporte, seguridad…). Es lo que se llama clasificación por programas.",
    capitulo: "Agrupa los gastos por su naturaleza (sueldos, servicios, obras, intereses…). Primero los grandes bloques (capítulos), dentro de cada uno su tipo concreto (artículos) y, al abrirlo, las partidas con el programa al que pertenecen. Es lo que se llama clasificación económica.",
  };

  function dibujar() {
    main.querySelector("#explica-modo").textContent = EXPLICA[modo];
    const raiz = buildTree(datos, modo);
    nodos = new Map();
    indexar(raiz);
    arbol.innerHTML = lista(raiz);
  }

  arbol.addEventListener("click", (e) => {
    const boton = e.target.closest("button.fila");
    if (!boton) return;
    const hijos = boton.nextElementSibling;
    const abrir = hijos.hidden;
    if (abrir && !hijos.innerHTML) hijos.innerHTML = lista(nodos.get(boton.dataset.id).hijos);
    hijos.hidden = !abrir;
    boton.setAttribute("aria-expanded", String(abrir));
    boton.querySelector(".nombre").firstChild.textContent = (abrir ? "▾ " : "▸ ") + boton.querySelector(".nombre").firstChild.textContent.slice(2);
  });

  main.querySelectorAll("[data-modo]").forEach((b) =>
    b.addEventListener("click", () => {
      modo = b.dataset.modo;
      main.querySelectorAll("[data-modo]").forEach((o) => o.setAttribute("aria-pressed", String(o === b)));
      dibujar();
    }),
  );

  main.querySelector("#buscar").addEventListener("input", (e) => {
    const consulta = e.target.value;
    const filas = buscar(datos, consulta);
    const activa = consulta.trim() !== "";
    arbol.hidden = activa;
    resultados.hidden = !activa;
    if (!activa) return;
    resultados.innerHTML = filas.length
      ? `<p class="muted">${filas.length} resultado(s)</p>` + tablaHtml(
          [{ texto: "Gasto" }, { texto: "Programa" }, { texto: "Tipo de gasto" }, { texto: `${anio - 1}`, num: true }, { texto: `${anio}`, num: true }],
          filas.map((f) => `<tr><td>${esc(f.nombre)}</td><td>${esc(f.programa)}</td><td>${esc(f.capitulo)}${f.articulo ? ` › ${esc(f.articulo)}` : ""}</td><td class="num">${formatEuros(f.anterior)}</td><td class="num">${formatEuros(f.actual)}</td></tr>`),
        )
      : `<p>No hay gastos que coincidan con «${esc(consulta)}».</p>`;
  });

  dibujar();
});
