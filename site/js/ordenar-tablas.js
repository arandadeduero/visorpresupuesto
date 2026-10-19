// Tablas ordenables: al pulsar una cabecera se ordena por esa columna; al crearse, cada tabla se ordena por la primera.
// La lógica (valorCelda, tipoColumna, ordenarFilas) es pura y se prueba con `node --test`; activarOrdenacion es el pegamento con el DOM.

const MILLONES = 1_000_000;
const FLECHAS = /^[▲▼＝●\s]+/;

/** Número que representa el texto de una celda («1.234 €», «−12,5 %», «2,2 M€», «27/11/2017»), o null si no es un número. */
export function valorCelda(texto) {
  if (typeof texto !== "string") return null;
  const t = texto.replace(/ /g, " ").replace(FLECHAS, "").trim();
  if (/sin cambios/i.test(t)) return 0;
  const fecha = t.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (fecha) return Number(fecha[3]) * 10000 + Number(fecha[2]) * 100 + Number(fecha[1]);
  const m = t.match(/^([+−-]?)\s*(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?\s*(M€|€|%)?(?:\s|$)/);
  if (!m) return null;
  const n = Number(`${m[2].replace(/\./g, "")}${m[3] ? "." + m[3] : ""}`) * (m[4] === "M€" ? MILLONES : 1);
  return m[1] === "−" || m[1] === "-" ? -n : n;
}

const esHueco = (t) => {
  const s = (t ?? "").trim().toLowerCase();
  return s === "" || s === "—" || s.startsWith("nuevo") || s.startsWith("desaparece");
};

/** «numero» si todas las celdas con contenido son números (los huecos como «—» o «nuevo» no cuentan), «texto» en otro caso. */
export function tipoColumna(textos) {
  const con = textos.filter((t) => !esHueco(t));
  return con.length > 0 && con.every((t) => valorCelda(t) !== null) ? "numero" : "texto";
}

const collator = new Intl.Collator("es", { numeric: true, sensitivity: "base" });

/** Copia ordenada de `filas` (cada una con `celdas: string[]`) por la columna `col`; los huecos van siempre al final y los empates conservan su orden. */
export function ordenarFilas(filas, col, dir = "asc") {
  const signo = dir === "desc" ? -1 : 1;
  const numerica = tipoColumna(filas.map((f) => f.celdas[col])) === "numero";
  return filas
    .map((fila, i) => ({ fila, i, v: numerica ? valorCelda(fila.celdas[col]) : (fila.celdas[col] ?? "").trim() }))
    .sort((a, b) => {
      const ha = numerica ? a.v === null : false;
      const hb = numerica ? b.v === null : false;
      if (ha || hb) return ha === hb ? a.i - b.i : ha ? 1 : -1;
      const c = numerica ? a.v - b.v : collator.compare(a.v, b.v);
      return c !== 0 ? signo * c : a.i - b.i;
    })
    .map((x) => x.fila);
}

const texto = (celda) => celda.textContent.replace(/\s+/g, " ").trim();

function preparar(tabla) {
  tabla.dataset.ordenable = "";
  const cabeceras = [...tabla.querySelectorAll("thead th")];
  const cuerpo = tabla.tBodies[0];
  if (!cuerpo || !cabeceras.length) return;
  const estado = { col: 0, dir: "asc" };

  const ordenar = (col, dir) => {
    estado.col = col;
    estado.dir = dir;
    const filas = [...cuerpo.rows];
    const fijas = filas.filter((f) => f.cells[0]?.tagName === "TH"); // filas de «Total»: siempre al final
    const ordenables = filas.filter((f) => !fijas.includes(f)).map((fila) => ({ fila, celdas: [...fila.cells].map(texto) }));
    ordenarFilas(ordenables, col, dir).forEach((x) => cuerpo.appendChild(x.fila));
    fijas.forEach((f) => cuerpo.appendChild(f));
    cabeceras.forEach((th, i) => th.setAttribute("aria-sort", i === col ? (dir === "asc" ? "ascending" : "descending") : "none"));
  };

  cabeceras.forEach((th, col) => {
    const nombre = texto(th);
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "orden";
    boton.title = `Ordenar por «${nombre}»`;
    boton.append(...th.childNodes);
    th.append(boton);
    boton.addEventListener("click", () => {
      if (estado.col === col) return ordenar(col, estado.dir === "asc" ? "desc" : "asc");
      const numerica = tipoColumna([...cuerpo.rows].filter((f) => f.cells[0]?.tagName !== "TH").map((f) => texto(f.cells[col] ?? f))) === "numero";
      ordenar(col, numerica && col > 0 ? "desc" : "asc"); // importes: de mayor a menor la primera vez
    });
  });
  ordenar(0, "asc");
}

/** Hace ordenables las tablas `table.datos` de `raiz`, también las que se añadan después (listas que se despliegan). */
export function activarOrdenacion(raiz) {
  const buscar = () => raiz.querySelectorAll("table.datos:not([data-ordenable])").forEach(preparar);
  new MutationObserver(buscar).observe(raiz, { childList: true, subtree: true });
  buscar();
}
