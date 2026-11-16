# Verification record

See `final-audit.md` for the full findings and the blocked live-route table.

- Python 3.12.14, Django 6.1.3, DRF 3.18.3; fresh virtual-environment installation succeeded.
- `python manage.py check`: zero issues. With `DJANGO_DEBUG=0` and an ephemeral strong secret, `check --deploy` reported only the optional HSTS preload warning; preload requires a real production-domain decision.
- `python manage.py test routes -v 1`: 20 passed, 0 failed (0.049 seconds test execution in the clean virtual environment). Routing responses in tests are mocked.
- CSV import: 8,151 total rows, 7,531 US rows, 6,626 US IDs, 487 US price conflicts. 6,045 approximate city positions; 581 unlocated.
- Local synthetic performance: 5,000 geometry points, 14 matched stations, 62.446 ms projection, 0.102 ms optimizer. This is not a live route benchmark.
- `ORS_API_KEY` was absent, so all three requested real routes returned HTTP 503 before any provider request. An unauthenticated HEAD probe to the provider domain failed with `URLError` from this workspace. No actual distance, duration, stop, or price result is claimed.

With the key loaded privately, run `python scripts/run_live_checks.py`. Its output distinguishes real provider calls from local application time and saves JSON under ignored `live_results/`.
