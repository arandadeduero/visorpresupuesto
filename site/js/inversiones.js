import { runPage, esc } from "./layout.js";
import { formatEuros } from "./format.js";
import { PALETTE } from "./charts.js";
import { filaHtml, tablaHtml } from "./ui.js";

const FUENTES = [
  ["prestamo", "Préstamo", "Dinero que se pediría prestado a un banco."],
  ["ingresosCorrientes", "Ingresos del Ayuntamiento", "Impuestos y tasas del año."],
  ["otros", "Otros", ""],
  ["rta", "Remanente de tesorería", "Ahorros de años anteriores."],
  ["subvenciones", "Subvenciones", "Dinero de otras administraciones para obras."],
];
const COLOR = Object.fromEntries(FUENTES.map(([k], i) => [k, PALETTE[i]]));

function miniBarra(proyecto) {
  const partes = FUENTES.filter(([k]) => proyecto[k] > 0);
  const barra = partes.map(([k, nombre]) => `<i style="flex:${proyecto[k]};background:${COLOR[k]}" title="${esc(nombre)}: ${formatEuros(proyecto[k])}"></i>`).join("");
  const texto = partes.map(([k, nombre]) => `${esc(nombre)} ${formatEuros(proyecto[k])}`).join(" · ");
  return `<div class="mini-barra" aria-hidden="true">${barra}</div><small class="muted">${texto || "—"}</small>`;
}

runPage("inversiones", async ({ anio, main, load }) => {
  const d = await load("inversiones");
  const usadas = FUENTES.filter(([k]) => d.fuentes[k] > 0);
  const programas = [...d.programas].sort((a, b) => b.total - a.total);
  const max = programas[0].total;

  main.innerHTML = `
    <h1>Inversiones: obras y compras <span class="muted">${anio}</span></h1>
    <p class="lead">El Ayuntamiento prevé invertir <strong>${formatEuros(d.total)}</strong> en obras, equipamientos y mejoras.</p>
    <h2>¿Cómo se pagan?</h2>
    <div class="stackbar" role="img" aria-label="Fuentes de financiación de las inversiones" style="min-height:40px">${usadas.map(([k, nombre]) => `<span class="seg" style="flex-grow:${d.fuentes[k]};background:${COLOR[k]};cursor:default;min-width:6px" title="${esc(nombre)}: ${formatEuros(d.fuentes[k])}"></span>`).join("")}</div>
    <ul class="leyenda">${usadas.map(([k, nombre, ayuda]) => `<li><i style="background:${COLOR[k]}"></i><strong>${esc(nombre)}</strong>: ${formatEuros(d.fuentes[k])} (${((d.fuentes[k] / d.total) * 100).toLocaleString("es-ES", { maximumFractionDigits: 1 })} %)${ayuda ? ` <span class="muted">· ${esc(ayuda)}</span>` : ""}</li>`).join("")}</ul>
    <div class="aviso"><h3>El préstamo es una previsión</h3>
      <p>Los <strong>${formatEuros(d.fuentes.prestamo)}</strong> de préstamo son lo máximo previsto en el presupuesto. Solo se pedirían si hacen falta, según la liquidación y la ejecución del presupuesto. El Ayuntamiento puede usar remanentes de tesorería (ahorros de años anteriores) para pagar parte de las obras, así que el préstamo final puede ser menor. Esta cifra es una estimación: depende de lo ya comprometido y de lo que finalmente no se ejecute. <a href="deuda.html?anio=${anio}">Ver la página de deuda</a>.</p></div>
    <h2>¿En qué se invierte?</h2>
    <p class="muted">Pulsa en cada línea para ver las obras y cómo se paga cada una.</p>
    <ul class="barras">${programas.map((p) => `<li>${filaHtml({
      id: p.codigo,
      nombre: p.nombre,
      importe: p.total,
      max,
      clicable: true,
      extra: `${p.proyectos.length} proyecto(s) · ${((p.total / d.total) * 100).toLocaleString("es-ES", { maximumFractionDigits: 1 })} % del total`,
    })}<div class="hijos" hidden></div></li>`).join("")}</ul>`;

  main.addEventListener("click", (e) => {
    const boton = e.target.closest("button.fila");
    if (!boton) return;
    const hijos = boton.nextElementSibling;
    const abrir = hijos.hidden;
    if (abrir && !hijos.innerHTML) {
      const p = d.programas.find((x) => x.codigo === boton.dataset.id);
      const proyectos = [...p.proyectos].sort((a, b) => b.importe - a.importe);
      hijos.innerHTML = tablaHtml(
        [{ texto: "Proyecto" }, { texto: "Importe", num: true }, { texto: "Cómo se paga" }],
        proyectos.map((x) => `<tr><td>${esc(x.nombre)}</td><td class="num">${formatEuros(x.importe)}</td><td>${miniBarra(x)}</td></tr>`),
      );
    }
    hijos.hidden = !abrir;
    boton.setAttribute("aria-expanded", String(abrir));
    const nombre = boton.querySelector(".nombre").firstChild;
    nombre.textContent = (abrir ? "▾ " : "▸ ") + nombre.textContent.slice(2);
  });
});
