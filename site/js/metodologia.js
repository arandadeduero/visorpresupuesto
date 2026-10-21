import { runPage } from "./layout.js";

// El texto vive en metodologia.html (<template>), así lo ve un rastreador sin JS y lo pinta el navegador sin duplicarlo.
// El build lo sustituye por el HTML ya montado en <main>; sin build se lee de la plantilla.
const montado = document.getElementById("contenido")?.cloneNode(true);
montado?.querySelectorAll("noscript").forEach((n) => n.remove());
const contenido = montado?.innerHTML || document.getElementById("contenido-estatico")?.innerHTML || "";

runPage("metodologia", async ({ main }) => {
  main.innerHTML = contenido;
});
