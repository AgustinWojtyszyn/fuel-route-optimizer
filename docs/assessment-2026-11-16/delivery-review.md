# Revisión independiente de entrega

Revisión de la referencia `7d6633add0a9cb92794c2df0520f821b2ef468e6`, realizada el 16/11/2026 por el agente de revisión de entrega, separado de los responsables del backend y de la interfaz. El informe se limita a los aspectos y comandos realmente inspeccionados; no sustituye la revisión matemática o de navegador de los otros agentes.

## Diagnóstico priorizado

No se encontró un P0 demostrado en el contrato documental, la instalación actual ni la CI de la referencia.

**P1 pendiente externo: falta una credencial HeiGIT autorizada.** `bool(os.getenv('ORS_API_KEY'))` resultó `False`. Esto impide verificar las rutas reales solicitadas y grabar una demostración de resultados reales. No se realizó ninguna llamada al proveedor desde esta revisión. La ausencia de clave es una condición del entorno, no un resultado calculado ni una prueba de que el proveedor esté caído.

**P2 demostrado: recopilación de estáticos incompleta.** En la referencia, `config/settings.py:20` declara `STATIC_URL`, pero no `STATIC_ROOT`. La ejecución local de `python manage.py collectstatic --noinput --dry-run` produjo `ImproperlyConfigured: You're using the staticfiles app without having set the STATIC_ROOT setting to a filesystem path.` No afecta a `runserver` con DEBUG, pero impide preparar los nuevos recursos de la interfaz para un servidor de estáticos. Se comunicó al responsable de implementación para incorporar una ruta de salida e ignorarla en Git. El resultado final de esa corrección corresponde al registro consolidado de pruebas.

**P2 documental: evidencias históricas no son evidencias de la revisión actual.** `docs/verification.md` conserva una cifra inicial de 20 tests y pruebas de rendimiento de otra revisión. Deben leerse como históricas; el informe de esta evaluación registra sus propios conteos, tiempos y pendientes. No se deben reutilizar esos tiempos como rendimiento de HeiGIT ni dar por grabado el Loom.

No se recomienda reinstalar Hallmark ni cambiar las dependencias solo por su número de versión. Las versiones fijadas son reales y la instalación actual no tiene conflictos.

## Dependencias y privacidad

Se comprobaron las versiones instaladas: Django 6.1.3, Django REST Framework 3.18.3, httpx 0.28.1 y geonamescache 3.0.0. `python -m pip check` respondió `No broken requirements found.` Esto comprueba consistencia de metadatos en el entorno actual; no equivale a una instalación limpia en todos los sistemas operativos.

Las fuentes primarias confirman [Django 6.1.3, publicación de seguridad del 3/11/2026](https://www.djangoproject.com/weblog/2026/nov/03/security-releases/) y [DRF 3.18.3, publicación del 6/10/2026](https://www.django-rest-framework.org/community/release-notes/). No se afirmó que estas versiones sean ficticias ni se propuso un downgrade sin evidencia.

La búsqueda de archivos versionados `*.csv`, `*.sqlite3`, `.env*` y `*.zip` devolvió únicamente `.env.example`. `.gitignore` excluye las bases locales, CSV, ZIP, archivos de entorno y `live_results/`. No se imprimieron claves ni filas comerciales. Este chequeo del árbol actual no es una auditoría forense de todo el historial de Git.

## GitHub Actions comprobado

La ejecución [43978291363](https://github.com/AgustinWojtyszyn/fuel-route-optimizer/actions/runs/43978291363) corresponde exactamente a la referencia y terminó en `success`. Se consultaron tanto los estados de la ejecución como los jobs y sus pasos mediante GitHub.

- [tests (3.12)](https://github.com/AgustinWojtyszyn/fuel-route-optimizer/actions/runs/43978291363/job/133687858877): success.
- [tests (3.13)](https://github.com/AgustinWojtyszyn/fuel-route-optimizer/actions/runs/43978291363/job/133687859248): success.

Ambos jobs aprobaron instalación de dependencias, Django check/migraciones, pruebas independientes, integración Django, JSON OpenAPI, JavaScript inline de ambas páginas, JavaScript enlazado y compilación. `.github/workflows/ci.yml:38–45` ya incluía ambas comprobaciones JavaScript en la referencia; no había que reconstruir esa corrección. Evidencia reducida en [github-reference-ci.json](github-reference-ci.json).

La revisión consultó también las cinco ejecuciones más recientes: las tres fallas anteriores a `17df38d` fueron seguidas por dos ejecuciones aprobadas (`17df38d`, `7d6633a`). Eso no autoriza a afirmar que los cambios nuevos todavía no publicados tengan CI remota aprobada. Su SHA debe revisarse tras una publicación autorizada.

## OpenAPI, Postman y JavaScript

- `docs/openapi.json` es JSON válido. Se resolvieron sus 13 referencias locales `$ref`.
- Las seis solicitudes de la colección Postman tienen métodos y URLs documentados; sus cinco cuerpos POST son JSON válido con el contrato `start/finish` y `city/state`.
- La colección incluye Los Angeles → Las Vegas, Chicago → Denver y New York City → Miami. El nombre New York City es el registro de entrada del catálogo, no un resultado inventado.
- `python scripts/check_javascript.py` comprobó cuatro scripts inline ejecutables y el import map. `node --check routes/static/routes/landing.js` y `node --check routes/static/routes/theme.js` finalizaron sin errores.
- La colección no se importó en la aplicación de escritorio Postman ni se ejecutaron sus rutas contra HeiGIT. La validez estructural no prueba disponibilidad del proveedor ni cobertura del CSV.

No se cambiaron endpoints, esquema ni la colección porque no se demostró una discrepancia de contrato que lo justificara. Las comprobaciones matemáticas y de formato de respuesta pertenecen al registro backend.

## Preparación de estáticos

La entrega debe permitir:

```sh
python manage.py collectstatic --noinput --dry-run
python manage.py collectstatic --noinput
```

`STATIC_ROOT` solo define la salida de recopilación. No hace que Gunicorn sirva los estáticos, no configura un dominio ni publica el proyecto. Para un despliegue futuro se requiere un servidor o servicio de estáticos, una clave secreta privada, hosts permitidos y la configuración HTTPS apropiada. No se modificó producción durante esta evaluación.

## Loom y pendientes

Se actualizó [el guion definitivo](../loom-script.md) para demostrar la API, rutas corta/larga, mapa, costos, errores y pruebas sin presentar fixtures como respuestas reales. El guion indica qué mostrar si falta la clave y qué sigue pendiente para completar la evaluación. **No se grabó ni se publicó un video.**

Pendientes externos de esta revisión: clave autorizada y consultas reales a HeiGIT; métricas reales de las tres rutas; comprobación del acceso físico de cada parada; ejecución del Postman de escritorio; grabación y URL de Loom; CI del SHA final si se publica; configuración de producción si se decide desplegar.
