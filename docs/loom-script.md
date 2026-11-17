# Guion para Loom · Fuel Route Optimizer

**Duración aproximada:** 4 minutos y medio. La narración y las notas de pantalla están en español. Los nombres de los botones y campos se conservan tal como aparecen en la interfaz en inglés.

Antes de grabar, abrí la [landing](https://fuel-route-optimizer-dyth.onrender.com/), el [planificador](https://fuel-route-optimizer-dyth.onrender.com/demo/) y [GitHub Actions](https://github.com/AgustinWojtyszyn/fuel-route-optimizer/actions). Importá la [colección de Postman](../postman/Fuel-Routes.postman_collection.json) y probá las dos rutas válidas. La colección ya apunta a Render. Dejá Chicago → Denver calculado en la pestaña del planificador.

## 0:00–0:55 · Landing y simulador de autonomía

**En pantalla.** Mostrá la portada y el gráfico de 500 millas. Bajá hasta **What does 500 miles really mean?** y elegí **750 mi**.

> Hola, soy Agustín. Para esta prueba desarrollé Fuel Route Optimizer, una aplicación que calcula recorridos por carretera en Estados Unidos y estima dónde conviene cargar combustible.
>
> Arranco en la landing porque acá se puede entender el supuesto principal antes de calcular un viaje. El vehículo sale con el tanque lleno, con 50 galones, y rinde 10 millas por galón. Eso le da una autonomía máxima de 500 millas.
>
> Acá abajo dejé un simulador. Si elijo 750 millas, me muestra que consumiría 75 galones y necesitaría al menos una recarga. Es un ejemplo para entender la autonomía. Ahora les muestro qué pasa cuando calculamos un viaje real.

## 0:55–1:40 · Planificador y herramientas

**En pantalla.** Pasá al planificador. Mostrá los campos de origen y destino, los accesos rápidos y el resultado de Chicago → Denver. Tocá **View entire route**, seleccioná una parada numerada y mostrale al evaluador su ficha.

> En el planificador puedo elegir la ciudad y el estado de salida y de llegada. Los campos sugieren ciudades del catálogo y también dejé algunos recorridos listos para probar.
>
> Acá tengo Chicago a Denver. Puedo volver a encuadrar todo el recorrido con este botón y seleccionar una parada en el mapa. Para cada carga, la aplicación muestra la estación, cuántos galones recomienda comprar y cuánto costaría esa compra. Abajo queda el detalle de los costos. La interfaz también tiene selector de idioma y modo claro y oscuro.

## 1:40–2:25 · Ruta corta en Postman

**En pantalla.** Enviá **Short | Los Angeles to Las Vegas**. Mostrá el estado **200**, el tipo de geometría y la lista de paradas vacía. Plegá las coordenadas para dejar visibles los totales.

> Ahora hago la misma operación desde la API. El endpoint recibe origen y destino, y Django los valida contra el catálogo de ciudades. La ruta viene de openrouteservice y la respuesta trae las coordenadas en GeoJSON, que son las que usa el navegador para dibujar el recorrido.
>
> En este caso, de Los Ángeles a Las Vegas, el tanque inicial alcanza. Por eso la lista de paradas está vacía y el gasto en compras durante el viaje es cero. Igual podemos ver cuánto combustible se consumió del tanque inicial.

## 2:25–3:55 · Ruta larga, precios y llamadas

**En pantalla.** Enviá **Long | Chicago to Denver**. Abrí `leg_distances_miles`, una entrada de `stops`, `fuel` y `meta.routing_api_calls`. Usá los importes que devuelva tu consulta. Si `meta.cache_hit` muestra `true`, señalá las cero llamadas nuevas y mencioná las cifras de la prueba sin caché como referencia.

> Vuelvo a la ruta de Chicago a Denver, ahora desde Postman. Para un recorrido largo, la aplicación toma la ruta inicial, busca estaciones cercanas con ubicación revisada y consulta los precios del CSV de la prueba.
>
> En cada parada busca la siguiente estación más barata a la que puede llegar. Si la encuentra, compra lo necesario para alcanzarla. Si no, compra hasta el límite del tanque o lo que le falta para llegar. Con las paradas elegidas, vuelve a pedir el recorrido por carretera y calcula las compras otra vez usando las distancias reales de cada tramo.
>
> En esta prueba aparecieron cinco paradas. El gasto estimado en compras durante el viaje fue de 162 dólares con 25 centavos. El costo total estimado fue de 335 dólares con 20 centavos, porque también incluye el valor del combustible que se usó del tanque inicial.
>
> La ruta corta necesitó una consulta al proveedor y la larga, dos. El servicio puede usar una tercera para verificar una alternativa. Si repito una ruta que ya está en caché, la respuesta indica que no hizo nuevas consultas.

## 3:55–4:30 · Validación y cierre

**En pantalla.** Enviá **Invalid | Unknown US city and state pair**, mostrá el **422** y abrí la pestaña de pruebas de GitHub.

> Para cerrar, envío una ciudad que está fuera del catálogo. La API devuelve un error 422 y lo detecta antes de llamar al proveedor de rutas.
>
> Las pruebas verifican la autonomía, el cálculo de las compras y qué pasa cuando un desvío deja una estación fuera de alcance. Las recomendaciones dependen de las estaciones revisadas disponibles en el trayecto, y el JSON indica si el acceso vehicular está verificado. El código, la documentación y la colección de Postman están en el repositorio. Gracias por ver la demo.
