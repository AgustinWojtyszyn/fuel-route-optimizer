ship

Revisión independiente final, 16 de noviembre de 2026. No encontré defectos concretos que deban corregirse antes de entregar este pulido.

La página explica una herramienta de planificación de rutas y combustible en Estados Unidos. Lo que un visitante recuerda es el recorrido curvo conceptual de 0 a 500 millas, acompañado de las dos premisas: 50 galones y 10 mpg.

La dirección de `design.md` describe lo que está renderizado: landing editorial, esquema conceptual propio y planner cartográfico separado. No hay una segunda representación del mapa de la aplicación en la landing. El mayor desajuste con la idea es ninguno. El dibujo esquemático es una decisión expresa del usuario y no constituye un hallazgo.

La jerarquía y los cortes de línea son más deliberados después: el hero separa «Distance tells / half the story», el título del esquema deja de terminar en «miles» aislado y el resultado de consumo muestra 105 con la misma importancia que las 2 recargas. Los temas oscuro y claro mantienen contraste visual y una acción principal inequívoca. A 1280 × 800 entran titular, explicación y acción; a 1920 el contenedor conserva su ancho y aumenta los márgenes. No hay una sección de la página completa de 1440 sin contenido suficiente para justificar su espacio.

El planner conserva origen, destino, estados, inversión, ejemplos, cálculo, estilos de mapa, zoom, leyenda y advertencias. En 320 y 375 la densidad es razonable: el formulario precede al mapa y los controles se acomodan sin superposición. El enlace de marca permite volver a la presentación en móvil aunque el enlace textual Overview se oculte.

Comprobé directamente en Chrome headless a 320 px, en francés y portugués, las dos páginas: ancho del documento y del viewport de 320 px; botones de cálculo completos en una línea; selección de idioma y estilos de mapa sin recortes. El botón francés muestra íntegro «Calculer l’itinéraire et le carburant» y el portugués «Calcular rota e combustível». Las capturas temporales de esta comprobación se tomaron antes de terminar de cargar el mapa y se utilizaron exclusivamente para evaluar texto y controles; las capturas entregadas sí muestran el mapa cargado. `browser-results.json` registra por separado 629 comprobaciones y 112 estados, sin errores: es evidencia del ejecutor original, no 112 inspecciones visuales manuales mías.

Las cifras del ejemplo son coherentes: 50 × 10 = 500 millas; 1050 / 10 = 105 galones; ceil(1050 / 500) − 1 = 2 recargas mínimas partiendo lleno. Los textos distinguen aritmética conceptual, ruta real, ubicaciones aproximadas y precios sin fecha; no presentan estaciones verificadas ni precios en vivo. La fuente mantiene controles nativos, etiquetas asociadas, título accesible para el SVG, estados aria-pressed y región de resultados aria-live. Hay reglas de foco visible y reducción de movimiento. Esto no equivale a una auditoría completa con lector de pantalla.

Antes era algo más marcada la separación del lienzo del esquema respecto de su tarjeta, y la numeración 01–03 facilitaba referirse a una fila del método. No encontré una acción o información que el visitante pudiera encontrar o usar antes y ahora resulte materialmente más difícil. El espacio recuperado para el texto de las filas y la mayor legibilidad del selector móvil compensan esos cambios.

Evidencia visual inspeccionada: ambas páginas a 1440, 375 y 320 en ambos temas; landing adicional a 1280 oscuro y 1920 claro; comparación con las capturas anteriores de landing 1440 oscuro/375 claro y planner 1440 oscuro/320 claro. Leí HTML y las partes pertinentes de CSS/JS después de las capturas. No ejecuté llamadas al proveedor de rutas ni probé dispositivos físicos; no certifico esos entornos ni el estado visual de resultados de una ruta live.

No diluir: conservar el esquema conceptual de 500 millas, la distinción entre ilustración y mapa real, y las advertencias visibles sobre precios y ubicaciones aproximadas.
