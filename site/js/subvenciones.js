import { runPage, esc } from "./layout.js";
import { formatEuros, matches } from "./format.js";
import { filaHtml, variacionHtml, tablaHtml } from "./ui.js";

runPage("subvenciones", async ({ anio, main, load }) => {
  const d = await load("subvenciones");
  const programas = [...d.programas].sort((a, b) => b.actual - a.actual);
  const max = programas[0].actual;

  main.innerHTML = `
    <h1>Subvenciones <span class="muted">${anio}</span></h1>
    <p class="lead">El Ayuntamiento prevé dar <strong>${formatEuros(d.total)}</strong> a asociaciones y entidades por convenio (en ${anio - 1}: ${formatEuros(d.totalAnterior)}).</p>
    <div class="controles"><div class="pestanas" role="group" aria-label="Cómo ver las subvenciones">
      <button type="button" data-vista="actividad" aria-pressed="true">Por actividad</button>
      <button type="button" data-vista="entidad" aria-pressed="false">Por entidad</button></div></div>
    <section id="vista-actividad">
      <p class="muted">Agrupadas por el tipo de actividad subvencionada. Pulsa en cada línea para ver las entidades.</p>
      <ul class="barras">${programas.map((p) => `<li>${filaHtml({
        id: p.partida,
        nombre: p.programa,
        importe: p.actual,
        max,
        clicable: true,
        extra: `${p.items.length} entidad(es) · ${variacionHtml(p.actual, p.anterior)}`,
      })}<div class="hijos" hidden></div></li>`).join("")}</ul>
    </section>
    <section id="vista-entidad" hidden>
      <p><label>Buscar una entidad <input type="search" id="buscar" placeholder="Por ejemplo: Cruz Roja, Cáritas, club…" autocomplete="off"></label></p>
      <div id="entidades"></div>
    </section>`;

  const cab = [{ texto: "Entidad" }, { texto: "Para qué" }, { texto: `${anio - 1}`, num: true }, { texto: `${anio}`, num: true }];
  main.querySelector("#vista-actividad").addEventListener("click", (e) => {
    const boton = e.target.closest("button.fila");
    if (!boton) return;
    const hijos = boton.nextElementSibling;
    const abrir = hijos.hidden;
    if (abrir && !hijos.innerHTML) {
      const p = d.programas.find((x) => x.partida === boton.dataset.id);
      const items = [...p.items].sort((a, b) => b.actual - a.actual);
      hijos.innerHTML = tablaHtml(cab, items.map((i) => `<tr><td>${esc(i.entidad)}</td><td>${esc(i.objeto)}</td><td class="num">${formatEuros(i.anterior)}</td><td class="num">${formatEuros(i.actual)}</td></tr>`));
    }
    hijos.hidden = !abrir;
    boton.setAttribute("aria-expanded", String(abrir));
    const nombre = boton.querySelector(".nombre").firstChild;
    nombre.textContent = (abrir ? "▾ " : "▸ ") + nombre.textContent.slice(2);
  });

  const lista = main.querySelector("#entidades");
  const pintaEntidades = (consulta) => {
    const filas = d.entidades.filter((e) => matches(e.entidad, consulta));
    lista.innerHTML = filas.length
      ? `<p class="muted">${filas.length} entidad(es) · ${formatEuros(filas.reduce((s, e) => s + e.actual, 0))} en ${anio}</p>` + tablaHtml(
          [{ texto: "Entidad" }, { texto: `Recibe en ${anio}`, num: true }, { texto: `${anio - 1}`, num: true }, { texto: "Actividades" }],
          filas.map((e) => `<tr><td>${esc(e.entidad)}</td><td class="num">${formatEuros(e.actual)}</td><td class="num">${formatEuros(e.anterior)}</td><td>${esc(e.programas.join(", "))}</td></tr>`),
        )
      : `<p>No hay entidades que coincidan con «${esc(consulta)}».</p>`;
  };
  main.querySelector("#buscar").addEventListener("input", (e) => pintaEntidades(e.target.value));
  pintaEntidades("");

  main.querySelectorAll("[data-vista]").forEach((b) =>
    b.addEventListener("click", () => {
      main.querySelectorAll("[data-vista]").forEach((o) => o.setAttribute("aria-pressed", String(o === b)));
      main.querySelector("#vista-actividad").hidden = b.dataset.vista !== "actividad";
      main.querySelector("#vista-entidad").hidden = b.dataset.vista !== "entidad";
    }),
  );
});
