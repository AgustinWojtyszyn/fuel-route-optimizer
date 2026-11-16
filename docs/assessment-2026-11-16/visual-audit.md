# Revisión visual independiente inicial

Base inspeccionada: `7d6633add0a9cb92794c2df0520f821b2ef468e6`. Revisor: agente `visual_audit`, sin cambios en plantillas, estilos ni JavaScript de producción. Se leyó `design.md`, la skill Hallmark 2.0 y su procedimiento de rediseño. La dirección bloqueada distingue una landing editorial con esquema conceptual de la mesa cartográfica real; esa distinción se conserva.

## Lo observado en el producto real

La landing explica los supuestos y dirige al planificador. Su esquema está identificado como conceptual, y no presenta estaciones o resultados ficticios como reales. El planificador conserva un formulario legible, mapa funcional y advertencias sobre posiciones aproximadas. La familia visual oscura/clara es coherente entre ambas páginas. No corresponde sustituir la landing por otra captura del mismo mapa.

Las capturas iniciales están en `before/`: landing y planificador, 320, 375 y 1440 px, temas oscuro y claro. El navegador recorrió **48 estados** (dos páginas, tres anchos, dos temas, cuatro idiomas); no encontró desbordamiento horizontal del documento ni excepciones JavaScript. `before/browser-audit.json` conserva las mediciones. Esto es una auditoría inicial, no la matriz final de siete tamaños exigida por la misión.

## Hallazgos priorizados

No se encontró un P0 visual en los estados iniciales inspeccionados.

### P1: contraste de límites de controles

Los controles de la landing usan `--line` como borde, con contraste **1,52:1** frente a su fondo tanto en oscuro (`#30423a` sobre `#172320`) como en claro (`#c9d5c9` sobre blanco). El planificador claro declara el borde de entrada `#869b8e` sobre `#f5f3ee`, con **2,67:1**. Son valores inferiores a la referencia de 3:1 utilizada por Hallmark para el límite identificador de un campo. La herramienta confirmó el caso de la landing; el del planificador claro se comprobó numéricamente porque el render predeterminado solo observa el tema inicial oscuro.

Ubicación inicial: `routes/static/routes/landing.css:53`, `:56` y `routes/static/routes/theme.css:38`. Recomendación concreta: un token de borde de control distinto del separador decorativo, verificado sobre ambos fondos. No oscurecer todas las líneas de composición para resolver un problema de campos.

### P2: icono de cambio de tema permanece fijo

`routes/static/routes/theme.js:28` y `:29` asignan `.hidden` sobre elementos SVG. En este navegador la propiedad no refleja el atributo HTML `hidden`: el icono de luna mantiene `display:block` incluso con su propiedad `hidden=true`; el icono de sol conserva el atributo `hidden` y `display:none` cuando la propiedad pasa a `false`. El tema real y el texto sí cambian; lo incorrecto es la señal gráfica.

Reproducción: abrir `/`, cambiar tema y examinar `#themeToggle svg`. Corregir mediante `toggleAttribute('hidden', condición)` o una clase explícita y comprobar ambos sentidos del cambio en ambas páginas.

### P2: cifra de consumo pierde jerarquía y se separa de la unidad

`routes/static/routes/landing.css:120` aplica `.lab__result span` a todos los descendientes, incluido `#gallonsValue` dentro de `<strong>`. El valor de 105 galones termina con tamaño de etiqueta de 12 px y en una línea distinta de la unidad, mientras que el número de recargas usa la escala destacada. Es visible en las capturas desktop y móvil, en ambos temas.

Corregir el selector de etiqueta a hijo directo (`.lab__result > span`) y conservar la cifra y su unidad en una composición legible. Esto no altera la aritmética.

### P2: controles táctiles y rótulo de idioma demasiado ajustados

A 320 px, el toggle de landing mide 35×38 px, el selector de idioma 77×38 px y el slider tiene 30 px de alto. En el planificador, el intercambio mide 36×36 px y los botones de estilo de mapa 36 px de alto. La referencia de hit target de 44 px mejoraría su uso móvil sin agrandar todo el contenido.

`before/control-clipping.json` muestra que el selector portugués de landing tiene `scrollWidth=79` frente a `clientWidth=75`. No se detectó recorte interno de los botones de cálculo franceses/portugueses en la inspección inicial de 320 px. Es preferible conceder unos píxeles al selector antes de reducir su texto a 10 px.

### P2: detalles editoriales que Hallmark detecta correctamente

- La etiqueta `FUEL RANGE / CONCEPT DIAGRAM` está en mayúsculas y con tracking, aunque la advertencia conceptual es importante. Debe conservarse la información, en caso normal y sin tracking.
- Los índices `01/02/03` antes de cada subtítulo activan su regla de eyebrow. Pueden integrarse en la fila en lugar de funcionar como preencabezados decorativos.
- Hay un marco interior con fondo, borde y radio dentro de la figura ya enmarcada. Una única capa de contención haría más clara la ilustración y respondería al criterio de evitar tarjeta dentro de tarjeta.
- El aviso conceptual tiene 11 px; algunos textos de marca tienen 9–10 px. La advertencia merece 12 px; la marca no debe usarse como excusa para reducir otros textos funcionales.

No son errores de cálculo ni razones para inventar material nuevo. Son correcciones de composición y acceso dentro de la dirección existente.

## Hallmark ejecutado

Se usó la sintaxis oficial instalada, con archivos preparados para resolver las URLs virtuales de Django y la URL del servidor real:

```sh
HALLMARK_PUPPETEER=/tmp/fuel-browser CHROME_PATH=<Chrome local> \
node .agents/skills/hallmark/scripts/sloplint.mjs \
  docs/assessment-2026-11-16/audit/landing.html \
  --genre editorial --render --before --url http://127.0.0.1:8134/

HALLMARK_PUPPETEER=/tmp/fuel-browser CHROME_PATH=<Chrome local> \
node .agents/skills/hallmark/scripts/sloplint.mjs \
  docs/assessment-2026-11-16/audit/demo.html \
  --genre editorial --scope app --render --before --url http://127.0.0.1:8134/demo/
```

Resultados iniciales reales:

| Página | FAIL | REFLEX | WARN | NOTE |
| --- | ---: | ---: | ---: | ---: |
| Landing | 9 | 13 | 8 | 3 |
| Planificador | 1 | 4 | 0 | 0 |

Los registros completos están en `hallmark-before-landing.txt` y `hallmark-before-planner.txt`. Hay hallazgos repetidos entre archivo preparado y URL; estos números no representan defectos independientes.

La captura desde el archivo preparado de la landing registra un aviso de fallback de fuentes: las fuentes absolutas `/static/` no resuelven desde `file://`. Las capturas realizadas sobre el servidor real sí cargan las fuentes locales. No se presenta ese aviso como un fallo de carga de la aplicación real ni se oculta del informe bruto.

Los registros `--before` para comparar elementos conservados se guardaron en `before/landing-kept.json` y `before/planner-kept.json`. Cada ejecución reemplaza el registro global de Hallmark; debe restaurarse la copia correspondiente antes de usar `--kept` por página.

## Qué mantener en la corrección

Mantener el esquema conceptual de seis hitos con su aclaración, el selector funcional de distancia hipotética, el formulario de dos ciudades, los tres estilos del mapa, las advertencias y el contraste fuerte de la acción principal. La landing ya tiene identidad propia; una corrección debería mejorar jerarquía y legibilidad sin reconstruir funcionalidades sanas.

## Límites de esta revisión

Esta auditoría inicial no evalúa la precisión del optimizador ni una ruta real de HeiGIT, no prueba dispositivos físicos y no certifica las siete resoluciones finales. No incluye resultados de rutas ni precios comerciales en las capturas. El equipo principal ejecutará la matriz final y la revisión de backend por separado.
