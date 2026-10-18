import { runPage, esc } from "./layout.js";
import { formatEuros, matches } from "./format.js";
import { filaHtml, variacionHtml, tablaHtml } from "./ui.js";
import { pintaQuesito } from "./quesito.js";

const EXPLICACION = {
  1: "Impuestos que se pagan cada año, como el IBI (viviendas), el impuesto de vehículos o el de actividades económicas.",
  2: "El impuesto que se paga al hacer construcciones, instalaciones u obras.",
  3: "Lo que se paga por usar servicios municipales: agua, aparcamiento regulado (ORA), terrazas, licencias, cursos y actividades…",
  4: "Dinero que llega de otras administraciones (Estado, Junta…) para financiar servicios.",
  5: "Intereses de depósitos, alquileres y concesiones de bienes del Ayuntamiento.",
  6: "Venta de terrenos y otros bienes del Ayuntamiento.",
  7: "Subvenciones recibidas para hacer obras e inversiones.",
  8: "Ahorros de años anteriores (remanente de tesorería afectado a fondos europeos) y pequeños reintegros.",
  9: "Préstamos previstos para financiar inversiones. Se explican en la página de deuda.",
};

runPage("ingresos", async ({ anio, main, load }) => {
  const datos = await load("ingresos");
  const caps = [...datos.capitulos].sort((a, b) => b.y2026 - a.y2026);
  const total = caps.reduce((s, c) => s + c.y2026, 0);
  const max = caps[0].y2026;

  main.innerHTML = `
    <h1>¿De dónde sale el dinero? <span class="muted">${anio}</span></h1>
    <p class="lead">Ingresos previstos: <strong>${formatEuros(total)}</strong>. Pulsa en cada línea para ver de qué está hecha.</p>
    <div id="quesito"></div>
    <p><label>Buscar un ingreso <input type="search" id="buscar" placeholder="Por ejemplo: IBI, basuras, terrazas…" autocomplete="off"></label></p>
    <div id="arbol"><ul class="barras">${caps.map((c) => `<li>${filaHtml({
      id: `cap-${c.cap}`,
      nombre: c.corto,
      title: `Nombre oficial: ${c.oficial}`,
      importe: c.y2026,
      max,
      clicable: true,
      extra: `${((c.y2026 / total) * 100).toLocaleString("es-ES", { maximumFractionDigits: 1 })} % del total · ${variacionHtml(c.y2026, c.y2025)}`,
    })}<div class="hijos" hidden></div></li>`).join("")}</ul></div>
    <div id="resultados" hidden></div>`;

  pintaQuesito(main.querySelector("#quesito"), datos.capitulos, "Ingresos por tipo");
  const arbol = main.querySelector("#arbol");
  const resultados = main.querySelector("#resultados");
  const cab = [{ texto: "Concepto" }, { texto: `${anio - 2}`, num: true }, { texto: `${anio - 1}`, num: true }, { texto: `${anio}`, num: true }, { texto: "Cambio" }];
  const fila = (x) => `<tr><td>${esc(x.nombre)}</td><td class="num">${formatEuros(x.y2024)}</td><td class="num">${formatEuros(x.y2025)}</td><td class="num">${formatEuros(x.y2026)}</td><td>${variacionHtml(x.y2026, x.y2025, "")}</td></tr>`;

  arbol.addEventListener("click", (e) => {
    const boton = e.target.closest("button.fila");
    if (!boton) return;
    const cap = datos.capitulos.find((c) => `cap-${c.cap}` === boton.dataset.id);
    const hijos = boton.nextElementSibling;
    const abrir = hijos.hidden;
    if (abrir && !hijos.innerHTML) {
      const conceptos = [...cap.conceptos].filter((x) => x.y2026 || x.y2025 || x.y2024).sort((a, b) => (b.y2026 ?? 0) - (a.y2026 ?? 0));
      hijos.innerHTML = `<p class="ayuda">${esc(EXPLICACION[cap.cap])}</p>${tablaHtml(cab, conceptos.map(fila))}`;
    }
    hijos.hidden = !abrir;
    boton.setAttribute("aria-expanded", String(abrir));
    const nombre = boton.querySelector(".nombre").firstChild;
    nombre.textContent = (abrir ? "▾ " : "▸ ") + nombre.textContent.slice(2);
  });

  main.querySelector("#buscar").addEventListener("input", (e) => {
    const consulta = e.target.value;
    const activa = consulta.trim() !== "";
    arbol.hidden = activa;
    resultados.hidden = !activa;
    if (!activa) return;
    const filas = datos.capitulos.flatMap((c) => c.conceptos.filter((x) => matches(x.nombre, consulta)).map((x) => ({ ...x, cap: c.corto })));
    resultados.innerHTML = filas.length
      ? tablaHtml([...cab.slice(0, 1), { texto: "Tipo de ingreso" }, ...cab.slice(1)], filas.sort((a, b) => (b.y2026 ?? 0) - (a.y2026 ?? 0)).map((x) => fila(x).replace("</td><td class=\"num\">", `</td><td>${esc(x.cap)}</td><td class="num">`)))
      : `<p>No hay ingresos que coincidan con «${esc(consulta)}».</p>`;
  });
});
