import { runPage, esc } from "./layout.js";
import { formatEuros } from "./format.js";
import { parseImporte, repartoAportacion } from "./lecturas.js";
import { filaHtml } from "./ui.js";

runPage("calculadora", async ({ anio, main, load }) => {
  const gastos = await load("gastos");
  main.innerHTML = `
    <h1>¿A qué se destina lo que pago? <span class="muted">${anio}</span></h1>
    <p class="lead">Parte del presupuesto se financia con impuestos y tasas locales. Escribe lo que pagas al año (mira tus recibos) y verás cómo se repartiría en los gastos del Ayuntamiento.</p>
    <form id="formulario" class="formulario" autocomplete="off">
      <label>Impuesto de bienes inmuebles (IBI), al año <input type="text" inputmode="decimal" name="ibi" placeholder="Por ejemplo: 350"></label>
      <label>Impuesto de vehículos, al año <input type="text" inputmode="decimal" name="vehiculos" placeholder="Por ejemplo: 120"></label>
      <label>Otras tasas locales (basuras, agua, vado…), al año <input type="text" inputmode="decimal" name="tasas" placeholder="Por ejemplo: 200"></label>
    </form>
    <p class="cifra" id="total" aria-live="polite"></p>
    <div id="reparto"></div>
    <div class="aviso"><h3>Cómo leerlo</h3><p>Es un reparto <strong>proporcional y orientativo</strong>: los impuestos no se destinan a un servicio concreto, sino al conjunto del presupuesto. Aquí se reparte tu aportación en la misma proporción que el gasto previsto de cada política. Tampoco todo el gasto se paga con impuestos locales: también hay transferencias de otras administraciones y préstamos.</p></div>`;

  const total = main.querySelector("#total");
  const reparto = main.querySelector("#reparto");
  const formulario = main.querySelector("#formulario");
  const dibujar = () => {
    const f = new FormData(formulario);
    const suma = ["ibi", "vehiculos", "tasas"].reduce((s, k) => s + parseImporte(f.get(k)), 0);
    const filas = repartoAportacion(suma, gastos.politicas);
    if (!filas.length) {
      total.textContent = "";
      reparto.innerHTML = '<p class="muted">Escribe al menos un importe para ver el reparto.</p>';
      return;
    }
    total.innerHTML = `Tu aportación: ${formatEuros(suma)} al año`;
    const max = filas[0].importe;
    reparto.innerHTML = `<ul class="barras">${filas.map((x) => `<li>${filaHtml({ nombre: x.nombre, importe: x.importe, max })}</li>`).join("")}</ul>`;
  };
  formulario.addEventListener("input", dibujar);
  formulario.addEventListener("submit", (e) => e.preventDefault());
  dibujar();
});
