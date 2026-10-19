// Construcción del árbol de gastos y búsqueda. Funciones puras, sin DOM.
import { matches } from "./format.js";

const porImporte = (a, b) => b.actual - a.actual;
const suma = (items, campo) => items.reduce((s, x) => s + (x[campo] ?? 0), 0);
// Año anterior de un grupo: si a alguna partida le falta (el Excel no trae las inversiones del año anterior), no se puede comparar.
const sumaAnterior = (items) => (items.some((x) => x.anterior === null || x.anterior === undefined) ? null : suma(items, "anterior"));

function nodoPartida(p, detalle) {
  return {
    id: `p-${p.cap}-${p.programa}-${p.codigo ?? "total"}`,
    nombre: p.nombre,
    codigo: p.codigo,
    detalle,
    anterior: p.anterior,
    actual: p.actual,
    hijos: null,
  };
}

/**
 * modo "politica": políticas de gasto (Cultura, Deporte…) → programas → partidas (¿en qué se gasta?).
 * modo "capitulo": capítulos → artículos → partidas (¿qué tipo de gasto es?).
 * El capítulo 1 (personal) no baja de artículo: sus artículos son hojas.
 */
export function buildTree(datos, modo) {
  const capitulo = new Map(datos.capitulos.map((c) => [c.cap, c]));
  const programa = new Map(datos.programas.map((p) => [p.codigo, p]));

  if (modo === "politica") {
    const porPrograma = new Map();
    for (const p of datos.partidas) {
      if (!porPrograma.has(p.programa)) porPrograma.set(p.programa, []);
      porPrograma.get(p.programa).push(p);
    }
    const nodosPrograma = [...porPrograma].map(([codigo, partidas]) => {
      const info = programa.get(codigo);
      return {
        id: `prog-${codigo}`,
        nombre: info.nombre,
        politica: info.politica,
        anterior: sumaAnterior(partidas),
        actual: suma(partidas, "actual"),
        hijos: partidas
          .map((p) => nodoPartida(p, p.cap === 1 ? "Sueldos y cotizaciones (total del programa)" : capitulo.get(p.cap).corto))
          .sort(porImporte),
      };
    });
    return datos.politicas
      .map((pol) => {
        const hijos = nodosPrograma.filter((n) => n.politica === pol.codigo).sort(porImporte);
        return { id: `pol-${pol.codigo}`, nombre: pol.nombre, anterior: sumaAnterior(hijos), actual: suma(hijos, "actual"), hijos };
      })
      .sort(porImporte);
  }

  // capítulo → artículo → partida (el programa va como detalle de la partida). El personal se queda en el artículo.
  return datos.capitulos
    .map((c) => {
      const hijos = datos.articulos
        .filter((a) => a.cap === c.cap && a.actual !== 0)
        .map((a) => {
          const partidas = c.cap === 1 ? null : datos.partidas.filter((p) => p.cap === c.cap && p.articulo === a.codigo);
          return {
            id: `cap-${c.cap}-art-${a.codigo}`,
            codigo: a.codigo,
            nombre: a.nombre,
            oficial: a.oficial,
            anterior: a.anterior,
            actual: a.actual,
            hijos: partidas ? partidas.map((p) => nodoPartida(p, programa.get(p.programa).nombre)).sort(porImporte) : null,
          };
        })
        .sort(porImporte);
      return { id: `cap-${c.cap}`, nombre: c.corto, oficial: c.oficial, anterior: c.anterior, actual: c.actual, hijos };
    })
    .sort(porImporte);
}

/** Programas y partidas cuyo nombre contiene la consulta (sin tildes ni mayúsculas). */
export function buscar(datos, consulta, limite = 200) {
  if (!consulta || !consulta.trim()) return [];
  const capitulo = new Map(datos.capitulos.map((c) => [c.cap, c]));
  const programa = new Map(datos.programas.map((p) => [p.codigo, p]));
  const articulo = new Map(datos.articulos.map((a) => [`${a.cap}-${a.codigo}`, a]));
  const filas = [];
  for (const p of datos.programas) {
    if (matches(p.nombre, consulta)) filas.push({ tipo: "programa", nombre: p.nombre, programa: p.nombre, capitulo: "—", anterior: p.anterior, actual: p.actual });
  }
  for (const p of datos.partidas) {
    const prog = programa.get(p.programa);
    if (p.cap !== 1 && matches(p.nombre, consulta)) {
      filas.push({ tipo: "partida", nombre: p.nombre, programa: prog.nombre, capitulo: capitulo.get(p.cap).corto, articulo: articulo.get(`${p.cap}-${p.articulo}`).nombre, anterior: p.anterior, actual: p.actual });
    }
  }
  return filas.sort(porImporte).slice(0, limite);
}
