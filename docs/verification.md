> Historical verification record. For the 16 November 2026 assessment, use [the current report](assessment-2026-11-16/REPORT.md); the counts and timings below belong to earlier runs.

# Verification record

See `final-audit.md` for the full findings and the blocked live-route table.

- Python 3.12.14, Django 6.1.3, DRF 3.18.3; fresh virtual-environment installation succeeded.
- `python manage.py check`: zero issues. With `DJANGO_DEBUG=0` and an ephemeral strong secret, `check --deploy` reported only the optional HSTS preload warning; preload requires a real production-domain decision.
- `python manage.py test routes -v 1`: 20 passed, 0 failed (0.049 seconds test execution in the clean virtual environment). Routing responses in tests are mocked.
- CSV import: 8,151 total rows, 7,531 US rows, 6,626 US IDs, 487 US price conflicts. 6,045 approximate city positions; 581 unlocated.
- Local synthetic performance: 5,000 geometry points, 14 matched stations, 62.446 ms projection, 0.102 ms optimizer. This is not a live route benchmark.
- `ORS_API_KEY` was absent, so all three requested real routes returned HTTP 503 before any provider request. An unauthenticated HEAD probe to the provider domain failed with `URLError` from this workspace. No actual distance, duration, stop, or price result is claimed.

With the key loaded privately, run `python scripts/run_live_checks.py`. Its output distinguishes real provider calls from local application time and saves JSON under ignored `live_results/`.

## Actualización de verificación reproducible (16/11/2026)

Las pruebas automáticas ahora se ejecutan en Python 3.12 y 3.13 en GitHub Actions.
Incluyen 1.000 problemas de compra en una ruta fija comprobados frente a un
optimizador exhaustivo independiente, pruebas de integración de Django con
respuestas de rutas simuladas, comprobaciones de calidad del JSON OpenAPI,
validación JavaScript y compilación. Consultar el último resultado en:
https://github.com/AgustinWojtyszyn/fuel-route-optimizer/actions/workflows/ci.yml

Estas pruebas **no representan consultas reales a HeiGIT**. Para obtener
resultados de carreteras reales es necesario ejecutar `python scripts/run_live_checks.py`
con `ORS_API_KEY` privado y después confirmar visualmente el acceso a cada
estación. Los puntos de una localidad son aproximados y **no deben mostrarse
como ubicaciones exactas de surtidores**.
