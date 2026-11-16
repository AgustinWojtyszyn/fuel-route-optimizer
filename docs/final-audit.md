# Fase 3 — auditoría final (16 de noviembre de 2026)

> **Actualización posterior (16/11/2026):** Este archivo preserva los resultados
> del análisis inicial de Fase 3. Desde entonces se implementaron controles de
> combustible con precisión decimal, pruebas independientes por enumeración,
> conciliación de recibos, límite de solicitudes, corrección de GeoJSON 3D,
> OpenAPI, interfaz de demostración y automatización CI.
> Consultá [el historial de GitHub Actions](https://github.com/AgustinWojtyszyn/fuel-route-optimizer/actions/workflows/ci.yml)
> para ver los resultados actuales; los conteos y mediciones siguientes son
> históricos, no la última batería de pruebas. **No hay resultados reales de HeiGIT
> verificados ni coordenadas exactas de los surtidores.**

## Estado

**No apto todavía para afirmar verificación de extremo a extremo.** La aplicación se instala, importa datos, inicia, responde localmente y pasa 20 pruebas automatizadas. La clave de HeiGIT no está disponible en `ORS_API_KEY` y este entorno no alcanza `api.heigit.org` por red: ninguna de las tres rutas reales obtuvo distancia ni geometría del proveedor. Además, las ubicaciones de estaciones son centros de localidades, no accesos comprobados a surtidores. El código y la documentación están preparados para completar esa validación sin publicar secretos ni datos OPIS.

## Defectos corregidos

| Gravedad | Módulo | Hallazgo y corrección | Comprobación |
| --- | --- | --- | --- |
| Alta | `route_planner.py` | Una parada que perdía su compra tras recalcular la ruta podía seguir siendo un waypoint invisible. Ahora se recalcula sin ella con un máximo de tres consultas, o se devuelve error. | `test_unused_waypoint_requires_third_route`; tres llamadas simuladas, un solo marcador comprado. |
| Alta | `station_matching.py` | Cada estación recalculaba la longitud de la polilínea y examinaba todos los segmentos. Se indexa la geometría una vez en celdas y se proyectan solo segmentos próximos. | 5.000 vértices sintéticos, 14 candidatas: 62,446 ms de búsqueda y proyección en este entorno. Caso de borde de celda probado. |
| Media | `views.py`, `import_cities.py` | El caché no se invalidaba al actualizar el índice de ciudades y las estaciones conservaban coordenadas antiguas. La importación de ciudades actualiza estaciones y versión geográfica en una transacción; el caché usa ambos digestos. | `test_location_version_invalidates_cache`; reimportación real con conteos estables. |
| Media | `routing_client.py`, `fuel_optimizer.py` | Valores no finitos podían atravesar validaciones numéricas. Se rechazan antes de planificar o interpretar el proveedor. | Pruebas de `NaN` e `Infinity`. |
| Media | `config/settings.py`, `views.py` | Validación de despliegue y tipos de entrada incompletos. Se agregaron protecciones CSRF/X-Frame, configuración HTTPS de producción y entrada JSON exclusiva. | `manage.py check`, pruebas de 415; `check --deploy` con clave temporal y `DEBUG=0` solo advierte que HSTS preload no está activado. |
| Media | `demo.html` | El nombre de una estación se insertaba en HTML del marcador. Ahora se presenta como texto. | Inspección de plantilla, suite completa. |
| Baja | `route_planner.py` | Faltaban longitudes de piernas y una indicación explícita de acceso no verificado. Se exponen `leg_distances_miles`, combustible final y `station_access_verified: false`. | Prueba de regresión de ruta recalculada. |

## Datos y geografía

El CSV original tiene SHA-256 `c704371f141ded9c54df6c32d488a0ba2ceb589f88c936c967daa5330e0cd241`. Se reimportaron 8.151 filas, 7.531 de EE. UU. y 620 de Canadá; 6.626 estaciones únicas estadounidenses, 26 filas completamente duplicadas y 487 estaciones estadounidenses con precios distintos. GeoNames (localidades de al menos 500 habitantes) proporcionó 21.007 localidades de los 48 estados representados; 6.045 estaciones tienen `city_approx` (91,23 %) y 581 están sin ubicar.

Una inspección de las direcciones de los 6.626 ID encontró 3.525 con alguna referencia simultánea a autopista interestatal y salida; 3.365 con un único número de cada una. Hubo 626 claves repetidas de estado/autopista/salida, por lo que el texto por sí solo no identifica un surtidor. OpenInterstate publica datos de salidas y enlaces con lugares bajo ODbL, pero su archivo de datos no estuvo accesible desde este entorno. No se hicieron coincidencias viales verificadas, geocodificación masiva ni atribuciones de coordenadas exactas. La ruta secundaria pasa por centros de ciudad: comprueba distancia entre esos puntos, no acceso físico a la estación.

## Rutas reales solicitadas

| Ruta | HTTP local | Distancia real | Duración | Paradas | Galones | Recargas | Costo total | Consultas reales a HeiGIT | Tiempo local |
| --- | ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |
| Los Ángeles → Las Vegas | 503 | Bloqueada | Bloqueada | Bloqueadas | Bloqueados | Bloqueadas | Bloqueado | 0 | 0,0457 s |
| Chicago → Denver | 503 | Bloqueada | Bloqueada | Bloqueadas | Bloqueados | Bloqueadas | Bloqueado | 0 | 0,0022 s |
| Nueva York → Miami | 503 | Bloqueada | Bloqueada | Bloqueadas | Bloqueados | Bloqueadas | Bloqueado | 0 | 0,0018 s |

Todos respondieron `routing_not_configured`; se midieron con el cliente de pruebas de Django, no mediante una conexión HTTP externa. El endpoint `POST https://api.heigit.org/openrouteservice/v2/directions/driving-car/geojson` sigue documentado por HeiGIT; una solicitud HEAD sin credencial a su dominio falló con `URLError` desde este entorno, por lo que tampoco se verificó una respuesta real de la API. El valor codificado incluido en la conversación representa metadatos con campos `org`, `id`, `h`, no una clave `ORS_API_KEY` cargada en el entorno. No se guardó ni reprodujo.

## Pruebas y rendimiento

- Entorno original: `python manage.py test routes -v 1`: **20 aprobadas, 0 fallidas**, 0,049 s de ejecución en el entorno virtual limpio. Pruebas del cliente externo y trayectos simulados están etiquetadas en el código; no son respuestas reales de HeiGIT.
- Entorno virtual limpio: dependencias instaladas desde `requirements.txt`, `manage.py check` y las 20 pruebas aprobadas nuevamente.
- Reimportación real: 6.626 estaciones, 6.045 centros aproximados. La ciudad Los Angeles→Las Vegas se resolvió desde el índice local; búsqueda de dos ciudades 5,121 ms en la medición sintética.
- Geometría **artificial** de 5.000 vértices y 1.100 millas declaradas: proyección de candidatas 62,446 ms, 14 candidatas; optimizador 0,102 ms, tres compras sintéticas. No equivale al tiempo de una ruta real ni valida sus distancias.
- El visor presenta el GeoJSON que devuelve la misma respuesta API; no lanza una segunda consulta de rutas. El arranque del servidor de desarrollo y `manage.py check` se ejecutaron en Fase 2; en esta fase se volvió a comprobar `manage.py check` y la API mediante el cliente local.

## Completar la validación real

En una computadora con acceso de red a HeiGIT, cargar la **clave verdadera** en `ORS_API_KEY` del proceso sin guardarla en archivos versionados. Luego ejecutar `python scripts/run_live_checks.py`. El programa hará una petición fría para cada una de las tres rutas, contará las llamadas efectivas a HeiGIT, registrará tiempos y comprobará el balance del tanque tras cada pierna. Guarda las respuestas completas solo en `live_results/`, excluido de Git. Revisar visualmente las coordenadas de paradas y su acceso antes de entregar el video. Si el proveedor rechaza una ruta o la aproximación de estaciones impide planificarla, comunicar exactamente el fallo; no sustituirlo por una ruta simulada.

## Límites pendientes

1. Faltan la clave real en este entorno y conectividad saliente a HeiGIT. Las tres pruebas de proveedor y ejemplos JSON reales están bloqueados aquí; requieren una computadora con acceso a esa API.
2. No hay coordenadas verificadas de los accesos a las estaciones. El precio mínimo se optimiza sobre una línea con posiciones aproximadas; no se demuestra el mínimo global ni la accesibilidad de cada OPIS ID.
3. Las distancias de desvío hacia centros de ciudad se incluyen en la segunda ruta, pero un desvío a un surtidor exacto permanece desconocido. Las rutas que cruzan Canadá o exceden los límites del proveedor pueden fallar.
4. La API de desarrollo no incluye autenticación ni límites por usuario. La caché local no se comparte entre procesos.
