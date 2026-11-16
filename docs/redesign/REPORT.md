# Rediseño de Fuel Route Optimizer

Implementación sobre `main`, a partir de `f1a7602`. Fecha: 16 de noviembre de 2026. Se usó la skill local Hallmark 2.0 y su procedimiento `references/redesign.md`. El pedido posterior del usuario reemplazó explícitamente la paleta anterior: el resultado usa papel mineral, tinta marina y azul cobalto.

## Evidencia visual

Abrir [compare.html](compare.html) para ver las dos páginas antes y después, y sus versiones móviles. Las capturas del antes están en `before/`; las finales, en `after/`, a 375, 768, 1280 y 1440 píxeles. Son capturas de la aplicación Django funcionando, con sus recursos cartográficos reales. No se utilizaron maquetas dibujadas, datos comerciales, precios ni rutas simuladas para la landing.

La landing usa dos capturas auténticas del planificador inicial: una de la mesa completa y otra del mapa para la composición móvil. La atribución cartográfica permanece visible fuera del recorte. No quedan imágenes de reemplazo pendientes.

## Auditoría inicial

- `/` corresponde a `routes/templates/routes/landing.html`; `/demo/`, a `routes/templates/routes/demo.html`. La primera es una página pública y la segunda una pantalla de aplicación.
- Los archivos `tokens.css` y `base.css` existían, pero las páginas no los cargaban. Cada HTML definía su propio sistema; la demo acumulaba un segundo bloque oscuro sobre el primero.
- La landing presentaba un SVG de ruta esquemático, etiquetas en mayúsculas, dos llamadas visualmente llenas y tres tarjetas genéricas.
- La demo ofrecía las interacciones esenciales, pero con tipografía funcional demasiado pequeña, contraste irregular y un mapa parcialmente dibujado dentro de un contenedor mucho mayor. Las capturas iniciales muestran ese defecto.
- La búsqueda de ciudades manejaba respuestas vacías, pero ocultaba los errores y no comunicaba la espera.
- CI extraía scripts de ambas páginas, pero el bucle de Node solo comprobaba nombres `fuel_route_demo_*`.
- Antes de cambiar código, la suite original daba 21 pruebas independientes aprobadas y una falla entre las 46 pruebas Django. La prueba contaba tres apariciones literales de `role="combobox"`: dos elementos reales y una cadena de selector JavaScript. Se cambió el selector interno a `input[aria-autocomplete]`, conservando los dos controles y la prueba original.

Hallmark inicial: **352 FAIL, 133 REFLEX, 18 WARN**, incluyendo las comprobaciones renderizadas. El detalle está en [hallmark-before.txt](hallmark-before.txt). Los números son hallazgos de la herramienta, no defectos visuales independientes: el modo utilizado inspeccionó archivos y URLs, por lo que hay detecciones repetidas.

## Implementación

La landing pasó a una composición editorial con titular, una explicación corta, una acción principal y una vista grande del producto. El SVG se sustituyó por capturas reales. Las capacidades se presentan como texto factual con jerarquía tipográfica, sin tarjetas ni estadísticas inventadas. Se conservaron los enlaces existentes y los cuatro idiomas. Los cambios de copy están registrados en [copy-changes.md](copy-changes.md).

El planificador comparte tipografía y tokens con la landing. Se rediseñaron el panel de entrada, los campos de ciudad/estado, el intercambio de destinos, los ejemplos, los estilos del mapa, las cifras comparables y el desglose del tanque inicial. Los marcadores, ajuste de ruta y copia del resumen permanecen operativos. El mapa se adapta al contenedor con `ResizeObserver` y redimensionamiento de Leaflet/MapLibre; las reglas globales de imagen no restringen su canvas.

La búsqueda muestra carga, coincidencias, ausencia de resultados y error, con selección por teclado y atributos ARIA. Un error conserva la entrada manual. El cálculo comunica progreso y muestra un esqueleto de resultados; durante la solicitud se bloquean las entradas que podrían volver incoherente el resultado. Al finalizar o fallar se restablecen. Se conserva el estado de éxito sin compras adicionales y el desglose de resultados con paradas.

El sistema canónico vive en `routes/static/routes/{tokens,base,product}.css`. Los archivos CSS originales de raíz son importaciones de compatibilidad, evitando duplicar tokens. Bricolage Grotesque y Manrope se sirven localmente, con sus licencias OFL. `design.md` documenta el sistema. No se añadieron frameworks.

No se modificaron modelos, migraciones, servicios, endpoints, algoritmo, precisión, proveedores ni la estructura de sus solicitudes. Permanecen los supuestos de 500 millas y 10 MPG. Las advertencias principales del planificador se conservan literalmente en los cuatro idiomas.

## Validación

| Comprobación | Resultado |
| --- | --- |
| Pruebas Django originales | 46/46 aprobadas |
| Pruebas independientes originales | 21/21 aprobadas |
| Navegador Chrome 148 | 138 comprobaciones aprobadas; cero excepciones JS |
| Tamaños | 375, 768, 1280 y 1440 px; ambas páginas sin desbordamiento horizontal |
| Idiomas | Inglés, español, francés y portugués en ambas páginas |
| Autocompletado | Consulta real al catálogo, teclado, selección, vacío y error |
| Formularios/resultados | Intercambio, ejemplos, carga, error, reintento, éxito, cero compras, paradas, moneda y copia |
| Mapa | Recursos reales de OpenFreeMap, cambio de estilo, marcadores, enfoque y ajuste de ruta |
| JavaScript de ambas páginas | 3 scripts ejecutables válidos; import map JSON válido |
| Django check / migraciones | Sin errores / sin cambios |
| OpenAPI JSON / compileall / diff-check | Aprobados |
| Contrato de presentación | Enlaces, controles, IDs funcionales, carga de scripts, catálogos y avisos conservados |

Resultados completos: [browser-results.json](browser-results.json), [browser-test-output.txt](browser-test-output.txt), [django-tests.txt](django-tests.txt), [core-tests.txt](core-tests.txt) y [preserved-results.json](preserved-results.json).

Las pruebas de interfaz de resultados y fallos interceptan exclusivamente las respuestas locales del API con fixtures sintéticos identificados en el script. Estos fixtures no se incorporan al producto, a la base ni a las imágenes de la landing. El mapa y las consultas de ciudades exitosas/vacías usan los recursos reales. La suite Django conserva sus proveedores simulados originales.

## Hallmark final

- Landing: **0 FAIL, 0 REFLEX**; ver [hallmark-landing.txt](hallmark-landing.txt).
- Planificador, con `--scope app`: **0 FAIL, 0 REFLEX**; ver [hallmark-planner.txt](hallmark-planner.txt).
- Se ejecutaron `--render` y `--kept`. El render también examinó pliegues de 1280, 1440 y 1920 px, y páginas completas de 1440 y 375 px.
- Para las capturas de Chrome sin GPU se habilitó el renderizador de software SwiftShader y se capturó con un viewport de altura completa para mantener el canvas en el área visible. Esto evita un canvas vacío en la imagen por limitaciones del compositor del entorno, sin cambiar el código de producción.
- Las URLs `/static/` de Django no son rutas del sistema de archivos. `prepare_hallmark_audit.py` prepara copias equivalentes con referencias locales resolubles para la capa estática; la capa visual examina las páginas reales del servidor. No se modificó Hallmark ni se desactivaron sus reglas.
- Los dos avisos `kept` restantes por ejecución corresponden a las rutas de archivos originales y a la otra URL del registro inicial, ya que se revisó cada página con su alcance apropiado y archivos preparados. La verificación adicional `verify_preserved.py` compara directamente los HTML originales de `f1a7602` con los actuales: todos los enlaces y controles originales permanecen. Solo se retira el ID `grid` del SVG eliminado por pedido del usuario.
- La advertencia sobre pocas secciones fue descartada con motivo registrado: se conservan tres regiones factuales en lugar de multiplicar información o inventar material. Los espaciados de la landing y de la mesa de trabajo se justifican en el registro F15 del CSS. La herramienta anota una ventana de 88 palabras, cercana a su presupuesto orientativo.
- Revisión visual final **en este hilo**, sin atribuirla a un revisor independiente: se resolvieron el mapa parcial, el recorte móvil de la captura, el contraste del foco en la cabecera oscura y la atribución del mapa. La página anterior hacía más evidente el límite del panel mediante su fondo oscuro; el diseño nuevo usa separación espacial y una línea, manteniendo el formulario identificable. No se detectó pérdida de una acción anterior.

## Reproducción

```sh
.venv/bin/python manage.py runserver 127.0.0.1:8127 --noreload
# En otra terminal:
.venv/bin/python manage.py test routes -v 1
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_javascript.py
.venv/bin/python scripts/verify_preserved.py
# Puppeteer se instala fuera del proyecto para esta auditoría:
npm install --prefix /tmp/fuel-browser puppeteer@24.43.1
FUEL_BROWSER_MODULE=/tmp/fuel-browser/node_modules/puppeteer node scripts/test_presentation.cjs
.venv/bin/python scripts/prepare_hallmark_audit.py
# Definir HALLMARK_PUPPETEER y CHROME_PATH según la instalación local.
node .agents/skills/hallmark/scripts/sloplint.mjs docs/redesign/audit/landing.html --genre editorial --render --kept --url http://127.0.0.1:8127/
node .agents/skills/hallmark/scripts/sloplint.mjs docs/redesign/audit/demo.html --genre editorial --scope app --render --kept --url http://127.0.0.1:8127/demo/
```

## Límites de esta entrega

No se ejecutó una consulta de optimización contra HeiGIT en vivo porque el entorno no dispone de credenciales de proveedor. No se verificaron precios actuales ni estaciones individuales, y no se publicaron datos comerciales. La automatización cubre Chrome de escritorio con ventanas de los cuatro anchos; no sustituye pruebas de dispositivo físico en Safari/iOS o Android. CI quedó corregida y sus pasos se reprodujeron localmente; no se ejecutó GitHub Actions remoto. Los cambios se guardan en `main` local, sin push ni despliegue remoto.
