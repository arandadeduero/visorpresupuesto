# Presupuestos que solo existen en PDF

De 2018, 2021, 2022 y 2023 el Ayuntamiento publicó el presupuesto completo en PDF (`<año>/Presupuesto <año>.pdf`), sin los Excel de los anexos. Estos scripts copian sus tablas a los mismos Excel que usan los años siguientes (A1, A2, A3, A9, A12, A13.1, A13.2), para que `tools/convert.py` los lea igual.

```sh
pdftotext -layout "2018/Presupuesto 2018.pdf" /tmp/2018.txt
.venv/bin/python -I tools/desde_pdf/extraer_2018.py /tmp/2018.txt 2018/
.venv/bin/python tools/convert.py 2018
```

Cada script comprueba lo extraído contra los subtotales y totales del propio PDF (programa, artículo, capítulo y resumen) y se para si algo no cuadra. Las erratas del PDF que no cambian importes (rótulos de total con otro código, por ejemplo) están comentadas en cada script.

2019 y 2020 no tienen presupuesto propio: se prorrogó el de 2018 (`PRORROGADOS` en `tools/convert.py`).
