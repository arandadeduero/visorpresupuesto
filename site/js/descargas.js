import { runPage } from "./layout.js";
import { descargasHtml } from "./descargas-html.js";

runPage("descargas", async ({ indice, main }) => {
  main.innerHTML = descargasHtml(indice);
});
