import { runPage, esc } from "./layout.js";

const TERMINOS = [
  ["Presupuesto inicial", "Lo que el Ayuntamiento prevé ingresar y gastar durante el año, aprobado antes de que empiece. Son previsiones: durante el año puede modificarse y lo realmente gastado puede ser distinto."],
  ["Ingresos", "El dinero que el Ayuntamiento espera recibir: impuestos, tasas, transferencias de otras administraciones, préstamos…"],
  ["Gastos", "El dinero que el Ayuntamiento prevé destinar a sueldos, servicios, ayudas, obras, intereses y devolución de préstamos."],
  ["Capítulo", "La manera de clasificar ingresos y gastos según su naturaleza. Hay nueve: por ejemplo, el capítulo 1 de gastos son los sueldos y el 6 las inversiones. Es lo que se llama clasificación económica."],
  ["Programa y política de gasto", "La manera de clasificar los gastos según su finalidad: cultura, deporte, seguridad, limpieza… Una política agrupa varios programas. Es lo que se llama clasificación por programas."],
  ["Partida", "La línea más concreta del presupuesto: un tipo de gasto dentro de un programa, por ejemplo «Energía eléctrica» del alumbrado público."],
  ["Gastos de personal", "Sueldos y cotizaciones sociales de las personas que trabajan en el Ayuntamiento."],
  ["Servicios y mantenimiento", "Los gastos corrientes en bienes y servicios: luz, agua, limpieza, mantenimiento, contratos, material."],
  ["Transferencias y ayudas", "Dinero que el Ayuntamiento da a otras entidades o personas, por ejemplo subvenciones a asociaciones."],
  ["Inversiones", "Obras y compras que duran en el tiempo: calles, edificios, instalaciones, vehículos."],
  ["Subvención nominativa", "Ayuda que el presupuesto asigna con nombre y apellidos a una entidad concreta para una actividad concreta."],
  ["Préstamo", "Dinero que el Ayuntamiento pide a un banco y devuelve con intereses en varios años."],
  ["Deuda viva", "Lo que queda por devolver de los préstamos en una fecha concreta."],
  ["Amortización", "La parte de un préstamo que se devuelve cada año (el dinero prestado, sin contar los intereses)."],
  ["Intereses", "Lo que se paga al banco por el préstamo, además de devolver el dinero. Si el tipo es variable, depende del Euribor."],
  ["Carga financiera", "Lo que se paga en un año por la deuda: intereses más amortización."],
  ["Remanente de tesorería", "Ahorros que el Ayuntamiento acumula de años anteriores. Se puede usar para pagar inversiones en lugar de pedir un préstamo."],
  ["Ingresos corrientes", "Los ingresos de cada año que no son préstamos ni ventas de bienes: impuestos, tasas, transferencias corrientes e ingresos patrimoniales."],
  ["Ahorro bruto", "Ingresos corrientes menos los gastos corrientes (sueldos, servicios y ayudas, sin intereses). Es lo que queda para pagar la deuda e invertir."],
  ["Por habitante", "El importe dividido entre el número de habitantes del municipio. Sirve para comparar, pero no es lo que paga cada vecino."],
];

runPage("guia", async ({ anio, main }) => {
  main.innerHTML = `
    <h1>Guía: las palabras del presupuesto</h1>
    <p class="lead">Qué significan los términos que verás en esta web.</p>
    <dl class="glosario">${TERMINOS.map(([t, d]) => `<dt id="${esc(t.toLowerCase().normalize("NFD").replace(/[^a-z]+/g, "-"))}">${esc(t)}</dt><dd>${esc(d)}</dd>`).join("")}</dl>
    <p class="muted">¿Echas en falta alguna palabra? <a href="https://github.com/arandadeduero/visorpresupuesto/issues" rel="noopener">Cuéntanoslo</a>. Para ver los datos de ${anio}, vuelve al <a href="index.html?anio=${anio}">inicio</a>.</p>`;
});
