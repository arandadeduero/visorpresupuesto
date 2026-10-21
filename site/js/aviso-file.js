// Script clásico (no módulo): con doble clic (file://) el navegador bloquea los módulos y la página se quedaría en
// «Cargando…» para siempre. Avisamos de cómo abrirla. Está en un fichero propio, no en línea, por la política de
// seguridad de contenido (script-src 'self').
if (location.protocol === "file:") {
  document.addEventListener("DOMContentLoaded", function () {
    var p = document.querySelector(".cargando");
    if (p) p.textContent = "Abre la web desde un servidor, no haciendo doble clic en el fichero (por ejemplo: python3 -m http.server -d site).";
  });
}
