# Evaluación final de Fuel Route Optimizer — 16/11/2026

## A. Resumen ejecutivo y diagnóstico

Se partió de `7d6633add0a9cb92794c2df0520f821b2ef468e6` en `main`. `git fetch origin main` confirmó que no había commits posteriores y que el árbol estaba limpio. Se leyeron arquitectura, historial, README, sistema visual y documentación antes de modificar código. Se usó descubrimiento MCP y, cuando el índice no contenía los recursos actuales o el transporte dejó de responder, lectura de fuente actual.

No se reconstruyeron el optimizador, los temas, los idiomas, la CI ni la ilustración que ya funcionaban. La dirección bloqueada en `design.md` se conservó: landing editorial con recorrido conceptual, separada de la herramienta cartográfica real. Se trabajó con revisión independiente de backend, entrega y diseño.

| Prioridad | Evidencia inicial | Resolución |
| --- | --- | --- |
| P0 | Ninguno demostrado en las pruebas y fuentes revisadas | No se atribuye optimalidad global ni funcionamiento del proveedor sin evidencia |
| P1 | Error del API sin traducir y pérdida del estado de error al cambiar idioma | Traducción por códigos estables y conservación del estado semántico |
| P1 | Al editar una ciudad permanecían cifras/mapa/copias de la ruta anterior | Se invalidan resultados, marcadores y resumen al cambiar los datos |
| P2 | Advertencias del API en inglés dentro de resultados traducidos | Mensajes de seguridad conocidos localizados; advertencia adicional prudente para mensajes desconocidos |
| P2 | `ZZ` pasaba la validación de estado del navegador | Lista de códigos estadounidenses, validación y mensajes accesibles traducidos; entrada manual conservada |
| P2 | Iconos de tema no cambiaban: `SVGElement.hidden` no cambia el atributo | Se usa `toggleAttribute('hidden', ...)` |
| P2 | Cifra de galones heredaba estilo de etiqueta de 12 px | Selector directo del rótulo, número y unidad con jerarquía correcta |
| P2 | Bordes de controles con contraste insuficiente; selector portugués estrecho a 320 px | Bordes medidos, blancos ligeramente tintados, controles de 44 px y ancho de selector suficiente |
| P2 | El cliente del proveedor aceptaba booleanos como mediciones y resumen de distancia cero | Nuevas pruebas fallidas antes de corregir; respuesta controlada `routing_response` |
| P2 | El verificador aceptaba vehículos diferentes pero internamente consistentes | Exige 10 MPG, 50 galones, tanque inicial lleno y rango declarado de 500 millas |
| P2 | `collectstatic` fallaba por falta de `STATIC_ROOT` | Salida local `staticfiles/`, ignorada en Git; colección real de 42 recursos aprobada |
| Pendiente externo | No hay `ORS_API_KEY` | Cero solicitudes live; las tres rutas y sus métricas reales siguen pendientes |

Los seis fallos de interfaz se reprodujeron antes de corregir: [ui-before.txt](ui-before.txt). El mismo ejecutor pasa después: [ui-after.txt](ui-after.txt). La revisión de backend conserva la evidencia de las ocho fallas nuevas iniciales y sus correcciones: [backend-audit.md](backend-audit.md).

## B. Cambios por archivo

- `routes/services/routing_client.py`: rechaza booleanos como distancia/duración y un resumen no positivo; mantiene códigos, geometría, endpoints y límites existentes.
- `scripts/verification.py`: verifica que la evidencia corresponda al vehículo de la evaluación; mantiene comprobaciones activas con `python -O`.
- `tests/test_assessment_audit.py`: nueve pruebas nuevas, incluidas 750 comparaciones fraccionales con programación dinámica exhaustiva y fronteras de proveedor/verificación.
- `routes/tests/test_assessment_contract.py`: cuatro pruebas nuevas del API para cero compras, varias paradas, eliminación de waypoint y rechazo de un tramo verificado de 501 millas.
- `routes/templates/routes/demo.html`: códigos de error localizados; estado semántico conservado; advertencias traducidas; invalidación de resultados; datalist/validación de estados; ARIA traducido; etiqueta precisa del valor del combustible inicial **consumido**; actualización de colores de marcadores al cambiar tema manteniendo la cámara y el estilo elegido.
- `routes/static/routes/theme.js`: iconos SVG correctos y evento de cambio de tema compartido.
- `routes/templates/routes/landing.html`, `landing.js`, `landing.css`: se conserva el gráfico conceptual de cinco intervalos y seis hitos; caption factual sin mayúsculas espaciadas, menor anidamiento visual, sombra oscura eliminada, tipografía/cifras/controles y contraste corregidos. No se introduce una copia del planificador ni una carretera ficticia presentada como real.
- `routes/static/routes/theme.css`: contraste del tema claro, separación de tamaños tipográficos y controles táctiles del planificador.
- `config/settings.py`, `.gitignore`: colección de estáticos reproducible; no configuración ni despliegue de hosting de producción.
- `scripts/test_ui_regressions.cjs`: reproducción y comprobación de los seis defectos de interfaz con fixtures sintéticos aislados del producto.
- `scripts/test_assessment.cjs`: matriz real de navegador, temas, idiomas, persistencia, controles, aritmética y capturas.
- `scripts/prepare_hallmark_audit.py`: salida configurable y recursos locales resolubles para la herramienta; no altera el producto ni el linter.
- `README.md`, `docs/verification.md`, `docs/loom-script.md`: instrucciones actuales, distinción de evidencias históricas y guion definitivo honesto.
- `docs/assessment-2026-11-16/`: resultados auténticos, capturas, revisiones independientes y este informe.

No se modificaron los tests originales, el algoritmo de compras, la proyección de estaciones, la planificación de waypoints, los modelos, las migraciones, el esquema de respuesta, OpenAPI, Postman ni las versiones de dependencias. CI ya revisaba ambos JavaScript en la referencia: no se volvió a implementar una corrección existente.

## C. Validación técnica ejecutada

| Comando o prueba | Resultado real |
| --- | --- |
| Baseline: Django / independientes | 53 / 21 aprobadas |
| `python manage.py check` | Sin problemas |
| `python manage.py makemigrations --check --dry-run` | Sin cambios |
| `python manage.py test -v 1` | 57/57 aprobadas |
| `python -m unittest discover -s tests -v` | 30/30 aprobadas |
| `python -O -m unittest discover -s tests -q` | 30/30 aprobadas |
| `python scripts/check_javascript.py` | Cuatro scripts inline válidos e import map JSON válido |
| `node --check routes/static/routes/landing.js` | Aprobado |
| `node --check routes/static/routes/theme.js` | Aprobado |
| `node --check` de los dos ejecutores nuevos | Aprobado |
| `python -m pip check` | Sin conflictos de dependencias |
| `python -m json.tool docs/openapi.json` | JSON válido; revisión adicional de sus 13 referencias locales |
| `python -m compileall -q config routes scripts tests` | Aprobado |
| `python manage.py collectstatic --noinput` | 42 archivos preparados localmente; salida excluida de Git |
| `git diff --check` | Aprobado |
| `test_ui_regressions.cjs` | 6 comprobaciones aprobadas después de reproducir 6 fallas |
| `test_assessment.cjs` | 629 comprobaciones, 112 estados; cero excepciones JavaScript |
| `test_presentation.cjs` original | 138 comprobaciones aprobadas |
| `python scripts/run_live_checks.py` | Salida no exitosa controlada: falta clave, cero solicitudes externas |

Ejecutores de navegador: `FUEL_BROWSER_MODULE=/tmp/fuel-browser/node_modules/puppeteer`, servidor Django en `http://127.0.0.1:8134`. El ejecutor original utiliza además `BASE_URL` para apuntar a ese servidor. Puppeteer 24.43.1 se instaló fuera de las dependencias de ejecución del proyecto. Las mediciones usan Chrome 148 y el renderizador de software para WebGL del entorno.

Los logs están en [django-tests.txt](django-tests.txt), [core-tests.txt](core-tests.txt), [core-optimized-tests.txt](core-optimized-tests.txt), [browser-results.json](browser-results.json), [browser-output.txt](browser-output.txt), [legacy-browser-results.txt](legacy-browser-results.txt), [collectstatic.txt](collectstatic.txt) y [live-preflight.txt](live-preflight.txt).

## D. Validación visual e idiomas

La matriz cruza las dos páginas, cuatro idiomas, dos temas y siete tamaños: **320×720, 375×812, 430×932, 768×1024, 1280×800, 1440×900, 1920×1080**. Se comprobaron desbordamiento horizontal, texto interno de botones, selección, iconos y nombres accesibles del tema, primer ingreso en inglés/oscuro pese a un navegador configurado en francés y persistencia entre páginas/recargas. Se probaron ambos autocompletados por teclado, intercambio, ejemplos y tres estilos del mapa. La aritmética de la landing incluye la frontera de 500 millas sin una carga adicional.

La [comparación visual](compare.html) muestra desktop y móvil, oscuro y claro. Las capturas auténticas están en [before/](before/) y [after/](after/). El gráfico se identifica como conceptual; no contiene precios, estaciones ni resultados inventados del proveedor. El mapa carga los recursos reales de OpenFreeMap y conserva atribución. Las imágenes WebGL se capturan con un viewport de altura completa para evitar un canvas fuera del compositor. Los estados de éxito/error del API se prueban con fixtures exclusivamente de test y no se usan como prueba de rutas reales ni se incorporan a la landing.

Hallmark 2.0 se ejecutó conforme a la sintaxis instalada, con `--render` y `--kept`, alcance editorial para la landing y `--scope app` para el planificador. Se mantiene el sistema bloqueado y se aplica un **polish**, sin reemplazar la composición aprobada por el usuario.

| Página | Antes | Después |
| --- | --- | --- |
| Landing | 9 FAIL, 13 REFLEX, 8 WARN | 0 FAIL, 0 REFLEX, 0 WARN; 3 Finish respondidos y 7 notas de composición/copy |
| Planificador | 1 FAIL, 4 REFLEX | 0 FAIL, 0 REFLEX, 0 WARN |

La landing conserva 4/4 enlaces, 2/2 campos, 14/14 hooks de script, 8/8 títulos y 2/2 figuras. El planificador conserva 6/6 enlaces, 5/5 campos, 16/16 hooks y 6/6 títulos según los registros. Las notas de Hallmark hacen visibles la densidad de copy heredada y el cierre compacto; no se eliminan ni se presentan como aprobaciones inexistentes. Se justifican las diferencias de separación de columnas y pesos variables. Los controles, focos y avisos tienen contrastes revisados en ambos temas.

Comandos reproducibles:

```bash
python scripts/prepare_hallmark_audit.py --out docs/assessment-2026-11-16/audit --local-assets
# Definir HALLMARK_PUPPETEER y CHROME_PATH según la instalación local.
# Restaurar landing-kept.json o planner-kept.json de before/ a .hallmark/before.json antes de cada --kept.
node .agents/skills/hallmark/scripts/sloplint.mjs docs/assessment-2026-11-16/audit/landing.html --genre editorial --render --kept --url http://127.0.0.1:8134/
node .agents/skills/hallmark/scripts/sloplint.mjs docs/assessment-2026-11-16/audit/demo.html --genre editorial --scope app --render --kept --url http://127.0.0.1:8134/demo/
```

Las copias preparadas únicamente resuelven las rutas virtuales `/static/` para el análisis del sistema de archivos. No se modificó el linter. Se renderizaron también las URLs reales. Los informes completos son [hallmark-after-landing.txt](hallmark-after-landing.txt) y [hallmark-after-planner.txt](hallmark-after-planner.txt).

La [revisión visual independiente final](final-visual-review.md) dictaminó **ship**, sin defectos pendientes, e inspeccionó francés/portugués a 320 px además de desktop/móvil en ambos temas. La [auditoría visual inicial](visual-audit.md) separa los defectos demostrados de preferencias opcionales. No se probaron dispositivos físicos ni Safari/iOS.

## E. Backend y restricciones matemáticas

Las 1.000 comparaciones exhaustivas existentes se complementan con 750 casos fraccionales a 0,1 galones, precios decimales y combustible inicial parcial del optimizador genérico. El API de evaluación sigue saliendo con 50 galones. Se contrastan costo exacto o inviabilidad contra una programación dinámica que enumera todos los niveles del tanque; no reutiliza la elección greedy.

Se verificaron rango de 500 millas, 10 MPG, capacidad de 50 galones, no sobrellenado ni déficits, fronteras exactas, precios iguales, estación más barata fuera de alcance, rutas sin compras y con varias cargas. Las cargas/costos se reconcilian con recibos redondeados a centavos. Se diferencia dinero de compras nuevas del valor estimado del **combustible inicial consumido**, que no es necesariamente el valor de los 50 galones enteros.

Los nuevos contratos API prueban 1 llamada sin compras, 2 con varias paradas y 3 cuando se elimina un waypoint; también rechazo de un tramo de 501 millas. El cache mantiene el caso de cero llamadas. Se preservan errores controlados y la imposibilidad de presentar ubicaciones aproximadas como surtidores verificados.

El benchmark de 7.000 ofertas demoró aproximadamente 0,017–0,032 segundos de CPU local. No incluye base de datos ni red y **no es** una medición de latencia de HeiGIT. El límite público de waypoints continúa documentado. El algoritmo es óptimo sobre una secuencia fija de candidatos; no prueba optimalidad global sobre todas las carreteras ni acceso a surtidores reales.

Detalles y limitaciones en [backend-audit.md](backend-audit.md). Las tres rutas live (Los Angeles→Las Vegas, Chicago→Denver, New York City→Miami) no tienen distancia, duración, galones, costos ni latencia acreditados por esta ejecución: falta la clave. No se inventaron esos resultados.

## F. GitHub y publicación

La CI de la referencia se comprobó mediante GitHub: [ejecución 43978291363](https://github.com/AgustinWojtyszyn/fuel-route-optimizer/actions/runs/43978291363), ambos jobs Python 3.12/3.13 y todos sus pasos en `success`. La [revisión de entrega](delivery-review.md) y [evidencia JSON](github-reference-ci.json) detallan esa comprobación.

Los cambios nuevos se prueban localmente antes de los commits y de cualquier publicación. El estado de su CI remota se incorporará después de publicarlos; la aprobación de la referencia no se atribuye a código todavía no publicado. No se crean ramas ni se despliega producción. OpenAPI, colección y dependencias ya válidas se mantienen.

## G. Entrega y pendientes explícitos

Completados: correcciones de frontend/backend, cuatro idiomas, dos temas, pruebas originales y nuevas, matriz visual, capturas, auditorías independientes, esquema/colección validados estructuralmente, recursos estáticos preparados y [guion definitivo de Loom](../loom-script.md). No se grabó un video.

Pendientes externos: credencial HeiGIT autorizada; ejecución live de las tres rutas con mediciones y acceso/cuota real; ejecución de la colección en Postman contra esos resultados; grabación de Loom; prueba física/Safari si la evaluación la exige. La salida `staticfiles/` requiere un servidor de estáticos en un despliegue futuro: no constituye por sí misma una configuración de producción.

Los CSV, base SQLite, archivos privados y resultados comerciales permanecen excluidos de Git. No se publican precios derivados ni claves. Estos pendientes no se convierten en aprobaciones por haber pasado pruebas con proveedores simulados.
