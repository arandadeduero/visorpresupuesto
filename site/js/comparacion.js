// Lógica de la página «Comparar»: empareja las categorías de dos presupuestos y calcula diferencias. Funciones puras, sin DOM.
//
// Se compara siempre el importe `actual` (el presupuesto inicial) de cada año con el de otro año, nunca el `anterior`
// de un año con el `actual` del otro: los créditos del año anterior no coinciden con el presupuesto inicial de ese año.
//
// Equivalencias entre años (comprobadas con los datos de todos los ejercicios publicados):
//  - Políticas de gasto: el código de dos cifras (p. ej. «33» Cultura) significa lo mismo en todos los años. Una política
//    que solo está en un año se marca «nuevo» o «desaparece» (hoy: la 46, Investigación, desarrollo e innovación).
//  - Capítulos de gastos e ingresos: los nueve capítulos y su nombre no cambian.
import { calcularIndicadores } from "./lecturas.js";
import { formatEuros, formatVariation, etiquetaCapitulo } from "./format.js";

const esNumero = (n) => typeof n === "number" && Number.isFinite(n);
const EPS = 0.005;

const dividir = (v, d) => {
  if (!esNumero(v)) return null;
  if (d === undefined) return v;
  return esNumero(d) && d > 0 ? v / d : null;
};

/**
 * Empareja dos listas por clave. `divisorA`/`divisorB` (población) permiten comparar por habitante.
 * Devuelve filas { clave, nombre, a, b, delta, pct, estado } con estado: nuevo | desaparece | sube | baja | igual.
 * a/b son null si la categoría no existe (o no tiene importe) ese año; `pct` es null cuando no tiene sentido.
 */
export function emparejar(listaA, listaB, { clave, nombre, divisorA, divisorB }) {
  const mapa = new Map();
  const meter = (lista, lado, divisor) => {
    for (const item of lista) {
      const k = String(clave(item));
      const fila = mapa.get(k) ?? { clave: k, nombre: nombre(item), a: null, b: null };
      fila[lado] = dividir(item.actual, divisor);
      mapa.set(k, fila);
    }
  };
  meter(listaA, "a", divisorA);
  meter(listaB, "b", divisorB);
  return [...mapa.values()].map((f) => {
    const a = f.a ?? 0;
    const b = f.b ?? 0;
    const delta = b - a;
    let estado;
    if (a <= EPS && b > EPS) estado = "nuevo";
    else if (b <= EPS && a > EPS) estado = "desaparece";
    else if (Math.abs(delta) <= EPS) estado = "igual";
    else estado = delta > 0 ? "sube" : "baja";
    const pct = estado === "sube" || estado === "baja" ? (delta / Math.abs(a)) * 100 : estado === "igual" && a > EPS ? 0 : null;
    return { ...f, delta, pct: pct !== null && Number.isFinite(pct) ? pct : null, estado };
  });
}

const VISTAS = {
  politicas: { lista: (d) => d.gastos.politicas, clave: (p) => p.codigo, nombre: (p) => p.nombre },
  gastoCapitulos: { lista: (d) => d.gastos.capitulos, clave: (c) => c.cap, nombre: etiquetaCapitulo },
  ingresoCapitulos: { lista: (d) => d.ingresos.capitulos, clave: (c) => c.cap, nombre: etiquetaCapitulo },
};
export const NOMBRES_VISTA = Object.keys(VISTAS);

const poblacion = (d, modo) => (modo === "habitante" ? d.resumen.habitantes : undefined);

/** Filas comparadas de una vista ("politicas" | "gastoCapitulos" | "ingresoCapitulos") para los datos de dos años. */
export function filasVista(vista, datosA, datosB, modo) {
  const v = VISTAS[vista];
  return emparejar(v.lista(datosA), v.lista(datosB), { clave: v.clave, nombre: v.nombre, divisorA: poblacion(datosA, modo), divisorB: poblacion(datosB, modo) });
}

const ORDENES = {
  sube: (x, y) => y.delta - x.delta,
  baja: (x, y) => x.delta - y.delta,
  pct: (x, y) => (y.pct ?? -Infinity) - (x.pct ?? -Infinity),
  importe: (x, y) => Math.max(y.a ?? 0, y.b ?? 0) - Math.max(x.a ?? 0, x.b ?? 0),
  nombre: (x, y) => x.nombre.localeCompare(y.nombre, "es"),
};

/** Copia ordenada de las filas: "importe" (por defecto), "sube", "baja", "pct" o "nombre". */
export function ordenar(filas, criterio = "importe") {
  return [...filas].sort(ORDENES[criterio] ?? ORDENES.importe);
}

const importe = (v, modo) => (modo === "habitante" ? `${formatEuros(v)} por habitante` : formatEuros(v, { compact: true }));

/** Frase en lenguaje llano que explica el cambio de una fila entre el año A y el año B. */
export function frase(fila, anioA, anioB, { verbo, modo }) {
  const { nombre, a, b, delta, estado } = fila;
  if (estado === "nuevo") return `${nombre} no tenía dinero previsto en ${anioA}; en ${anioB} se prevé ${verbo} ${importe(b, modo)}.`;
  if (estado === "desaparece") return `${nombre} ya no tiene dinero previsto en ${anioB} (en ${anioA} se preveía ${verbo} ${importe(a, modo)}).`;
  if (estado === "igual") return `En ${nombre} se prevé ${verbo} ${importe(b ?? 0, modo)} en ${anioB}, igual que en ${anioA}.`;
  const cuanto = importe(Math.abs(delta), modo);
  return `En ${nombre} se prevé ${verbo} ${importe(b, modo)} en ${anioB}: ${cuanto} ${delta > 0 ? "más" : "menos"} que en ${anioA} (${formatVariation(b, a).text}).`;
}

/** Total de gastos o de ingresos de cada presupuesto y su diferencia. */
export function titular(datosA, datosB, que, modo) {
  const campo = que === "ingresos" ? "totalIngresos" : "totalGastos";
  const a = dividir(datosA.resumen[campo], poblacion(datosA, modo));
  const b = dividir(datosB.resumen[campo], poblacion(datosB, modo));
  const delta = esNumero(a) && esNumero(b) ? b - a : null;
  const pct = delta !== null && a > 0 ? (delta / a) * 100 : null;
  return { a, b, delta, pct };
}

/** Valor de una categoría en cada año (null si ese año no existe en esa categoría). `listaDatos`: [{anio, gastos, ingresos, resumen}]. */
export function serieEvolucion(listaDatos, vista, clave, modo) {
  const v = VISTAS[vista];
  return [...listaDatos]
    .sort((x, y) => x.anio - y.anio)
    .map((d) => {
      const item = v.lista(d).find((i) => String(v.clave(i)) === String(clave));
      return { anio: d.anio, valor: item ? dividir(item.actual, poblacion(d, modo)) : null };
    });
}

/** Pareja de años a comparar a partir de la URL: por defecto los dos últimos; nunca el mismo año dos veces. */
export function elegirPareja(anios, pedidoA, pedidoB) {
  const ordenados = [...anios].sort((x, y) => x - y);
  const valido = (p) => (ordenados.includes(Number(p)) && p !== null && p !== "" ? Number(p) : null);
  const ultimo = ordenados.at(-1) ?? null;
  const penultimo = ordenados.length > 1 ? ordenados.at(-2) : ultimo;
  const a = valido(pedidoA) ?? penultimo;
  let b = valido(pedidoB) ?? ultimo;
  if (a === b) b = [...ordenados].reverse().find((x) => x !== a) ?? null;
  return { a, b };
}

const INDICADORES = [
  ["ahorroBruto", "Ahorro bruto", "euros"],
  ["ahorroBrutoPct", "Ahorro bruto sobre los ingresos corrientes", "pct"],
  ["impuestosYTasasPorHabitante", "Impuestos y tasas por habitante", "euros"],
  ["dependenciaTransferenciasPct", "Dependencia de otras administraciones", "pct"],
  ["deudaViva", "Deuda a final de año (préstamos actuales)", "euros"],
  ["deudaPorHabitante", "Deuda por habitante", "euros"],
  ["deudaSobreIngresosCorrientesPct", "Nivel de endeudamiento (estimado)", "pct"],
  ["ahorroNetoEstimado", "Ahorro neto (estimado)", "euros"],
  ["cargaFinanciera", "Lo que cuesta la deuda al año", "euros"],
  ["cargaFinancieraPct", "Coste de la deuda sobre los ingresos", "pct"],
];

/** Indicadores de ambos años lado a lado. `entradaX` = { resumen, ingresos, deuda } de cada año (misma forma que calcularIndicadores). */
export function filasIndicadores(entradaA, entradaB) {
  const ia = calcularIndicadores(entradaA);
  const ib = calcularIndicadores(entradaB);
  return INDICADORES.map(([id, etiqueta, tipo]) => {
    const a = esNumero(ia[id]) ? ia[id] : null;
    const b = esNumero(ib[id]) ? ib[id] : null;
    return { id, etiqueta, tipo, a, b, delta: a !== null && b !== null ? b - a : null };
  });
}
