# Loom definitivo: demostración técnica verificable (5–6 minutos)

Este archivo es un **guion**, no una grabación. No hay una URL de video generado por esta revisión. Preparar una pantalla sin claves ni CSV privado y una consola con el entorno ya cargado. Nunca abrir `.env`, el gestor de claves, el archivo de precios o los JSON privados de `live_results/` durante la grabación.

## Preparación fuera de cámara

1. Seguir el README en un entorno local: instalar dependencias, migrar, importar ciudades y el CSV proporcionado por el evaluador. Cargar `ORS_API_KEY` únicamente como variable privada; `.env.example` no se carga automáticamente.
2. Ejecutar `python scripts/run_live_checks.py` con la clave válida y guardar los resultados **privadamente**. Debe verificar Los Angeles → Las Vegas, Chicago → Denver y New York City → Miami. Anotar estado HTTP, distancia, duración, paradas, galones, compras nuevas, valor inicial, tiempo y llamadas de cada ejecución. Si falla, investigar antes de grabar o mostrar el error real y declararlo pendiente.
3. Ejecutar las pruebas y tener visibles los resultados de esa ejecución. Consultar el SHA y la CI reales; una comprobación de un SHA anterior no acredita el código nuevo.
4. Importar `postman/Fuel-Routes.postman_collection.json`, definir `baseUrl` local y abrir `/` y `/demo/`. No incluir secretos en variables compartidas de Postman ni exportarlas.
5. Para medir llamadas en frío, usar las ejecuciones del script que limpia la caché de desarrollo. Una respuesta de caché debe mostrar `cache_hit: true` y cero llamadas, sin presentarla como una consulta nueva.

## 0:00–0:40 — Qué se evalúa

Mostrar el repositorio y el commit concreto. Explicar: Django/DRF recibe dos ciudades de EE. UU., obtiene una carretera de HeiGIT y calcula compras sobre la secuencia de estaciones candidatas del CSV. El vehículo sale con 50 galones, 500 millas de autonomía y 10 MPG. Los precios son observaciones sin fecha, no precios en vivo.

Abrir la CI del mismo SHA si ya existe y está aprobada. Si no existe una ejecución remota de ese SHA, mostrar las pruebas locales y decir que su CI remota está pendiente.

## 0:40–1:35 — API y ruta corta

En Postman, mostrar `/health/`: confirma catálogo local y presencia de clave, no autentica con HeiGIT. Ejecutar la solicitud Los Angeles → Las Vegas o la ruta corta de la colección.

Mostrar únicamente la respuesta obtenida en ese momento: geometría `LineString`, distancia, duración, `vehicle`, `fuel`, `meta.routing_api_calls` y `cache_hit`. Si la respuesta real no requiere una compra nueva, explicar la diferencia entre consumir combustible y comprarlo. No predecir una distancia o costo antes de recibirlos.

## 1:35–2:35 — Ruta larga y comprobación financiera

Ejecutar Chicago → Denver y, si el tiempo lo permite, New York City → Miami. Mostrar las paradas que la respuesta real recomiende, sus galones y recibos. Distinguir:

- `purchased_en_route_usd`: nuevas compras; coincide con la suma de los recibos mostrados.
- `initial_fuel_estimated_cost_usd`: valor de referencia del combustible inicial consumido, no un gasto nuevo.
- `estimated_total_trip_cost_usd`: ambas partidas.

Relacionar `leg_distances_miles` con la autonomía: ningún tramo puede exigir más combustible del disponible ni una compra superar los 50 galones. Mostrar el conteo real de llamadas: una para la ruta directa, normalmente dos con waypoints y máximo tres para retirar un waypoint sin compra. No prometer ese patrón si la respuesta concreta fue un error.

## 2:35–3:35 — Interfaz y mapa

Mostrar brevemente la landing: ilustración conceptual explícita, supuestos y acción al planificador. No describir el esquema como una carretera real.

En `/demo/`, buscar origen/destino con teclado, seleccionar ciudad/estado y calcular una de las rutas comprobadas. Mostrar mapa, zoom/estilo, resumen, una parada, enfoque del marcador y copia del resumen. Cambiar oscuro/claro e idioma después del resultado para demostrar persistencia y traducción de datos dinámicos.

Decir y señalar la advertencia: **los puntos representan localidades aproximadas; no son entradas a surtidores verificadas**. La optimización es sobre la secuencia fija de candidatos, sin prueba de optimalidad global entre todas las carreteras.

## 3:35–4:15 — Errores y límites

Mostrar una solicitud mal formada de forma controlada (por ejemplo, estado de tres letras: 400) y una ciudad inexistente (422). Si no hay catálogo o cobertura viable, mostrar el código real devuelto, sin sustituirlo por paradas falsas. Explicar que los errores de proveedor conservan un contrato JSON y no producen un itinerario inventado.

## 4:15–5:20 — Pruebas y evidencia

En consola, ejecutar o mostrar el registro auténtico de:

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test -v 1
python -m unittest discover -s tests -v
python scripts/check_javascript.py
node --check routes/static/routes/landing.js
node --check routes/static/routes/theme.js
```

Mostrar la prueba exhaustiva sobre casos sintéticos y explicar que permite contrastar el costo de una secuencia fija con un oráculo independiente. No presentarla como evidencia de disponibilidad actual de HeiGIT. Mostrar las capturas de navegador, tamaños, temas e idiomas efectivamente comprobados y el informe Hallmark con sus avisos o pendientes.

## 5:20–5:50 — Entrega honesta

Mostrar README, OpenAPI, colección Postman y el informe de la revisión. Señalar las limitaciones concretas del entorno y del modelo. Compartir repositorio y URL real de Loom solo después de grabar. Mantener privados el CSV, claves y resultados derivados que no tengan autorización de redistribución.

## Si falta clave o HeiGIT no responde

No se puede demostrar una ruta real completa. Grabar, si se desea, un recorrido de arquitectura, interfaz y pruebas locales, etiquetándolo como tal; mostrar el error controlado del entorno y el resultado del script sin clave. Dejar explícitamente pendientes las tres rutas reales, tiempos/costos/llamadas medidos y el video completo de evaluación. **No reproducir un fixture en pantalla afirmando que es una respuesta de HeiGIT.**
