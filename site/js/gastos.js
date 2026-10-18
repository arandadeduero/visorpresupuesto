import { runPage, esc } from "./layout.js";
import { formatEuros } from "./format.js";
import { buildTree, buscar } from "./gastos-tree.js";
import { filaHtml, variacionHtml, tablaHtml } from "./ui.js";
import { pintaQuesito } from "./quesito.js";

runPage("gastos", async ({ anio, main, load }) => {
  const datos = await load("gastos");
  const total = datos.capitulos.reduce((s, c) => s + c.y2026, 0);
  let modo = "programa";
  let nodos = new Map();

  main.innerHTML = `
    <h1>¿En qué se gasta el dinero? <span class="muted">${anio}</span></h1>
    <p class="lead">Total previsto: <strong>${formatEuros(total)}</strong>. Pulsa en cada línea para ver su detalle.</p>
    <div id="quesito"></div>
    <div class="controles">
      <div class="pestanas" role="group" aria-label="Cómo agrupar los gastos">
        <button type="button" data-modo="programa" aria-pressed="true">¿En qué se gasta?</button>
        <button type="button" data-modo="capitulo" aria-pressed="false">¿Qué tipo de gasto es?</button>
      </div>
    </div>
    <p><label>Buscar un gasto <input type="search" id="buscar" placeholder="Por ejemplo: energía, parques, cultura…" autocomplete="off"></label></p>
    <div id="arbol"></div>
    <div id="resultados" hidden></div>
    <div class="ayuda"><strong>Sobre el personal:</strong> los sueldos y cotizaciones se muestran agrupados por programa, sin detalle por categoría. El resto de gastos llega hasta la partida concreta.</div>`;

  pintaQuesito(main.querySelector("#quesito"), datos.capitulos, "Gastos por tipo de gasto");
  const arbol = main.querySelector("#arbol");
  const resultados = main.querySelector("#resultados");

  const indexar = (lista) => lista.forEach((n) => { nodos.set(n.id, n); if (n.hijos) indexar(n.hijos); });

  function lista(hijos) {
    const max = Math.max(...hijos.map((n) => n.y2026), 1);
    return `<ul class="barras">${hijos.map((n) => `<li>${filaHtml({
      id: n.id,
      nombre: n.nombre,
      title: n.oficial ? `Nombre oficial: ${n.oficial}` : undefined,
      importe: n.y2026,
      max,
      clicable: Boolean(n.hijos),
      extra: [n.detalle ? esc(n.detalle) : "", `${((n.y2026 / total) * 100).toLocaleString("es-ES", { maximumFractionDigits: 1 })} % del total`, variacionHtml(n.y2026, n.y2025)].filter(Boolean).join(" · "),
    })}<div class="hijos" hidden></div></li>`).join("")}</ul>`;
  }

  function dibujar() {
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
          filas.map((f) => `<tr><td>${esc(f.nombre)}</td><td>${esc(f.programa)}</td><td>${esc(f.capitulo)}</td><td class="num">${formatEuros(f.y2025)}</td><td class="num">${formatEuros(f.y2026)}</td></tr>`),
        )
      : `<p>No hay gastos que coincidan con «${esc(consulta)}».</p>`;
  });

  dibujar();
});
