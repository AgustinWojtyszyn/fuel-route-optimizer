# Backend Django Engineer — assessment submission handoff

**Project:** US Fuel Route Planner  
**Code:** `main` of [AgustinWojtyszyn/fuel-route-optimizer](https://github.com/AgustinWojtyszyn/fuel-route-optimizer)  
**Runtime:** Python 3.12+, Django 6.1.3, Django REST Framework 3.18.3

## Assessment requirements: implemented scope

| Requirement | Demonstrable artifact |
| --- | --- |
| API accepts a US start and finish | `POST /api/v1/routes/optimize/`; structured `{city,state}` or `"City, ST"` inputs, checked against local US gazetteer |
| Returns a road route and a map | Complete GeoJSON `LineString` in `route.geometry`; interactive map at `/demo/` |
| Finds cost-effective places to buy fuel | Source CSV is imported into SQLite; candidate stations projected to a route; fixed-route fuel purchase optimizer |
| Vehicle range 500 miles; 10 MPG | 50-gallon full starting tank; range checked after each returned road leg |
| Reports total fuel cost | Purchases, gallons, per-stop receipts, estimated cost of initial fuel consumed and reconciled overall estimate |
| Free routing API | openrouteservice/HeiGIT Standard key; one call for direct route, typically two with fuel stops, maximum three |
| Latest stable Django | Pinned Django 6.1.3 (November 2026 security release) |
| Fast API and few routing calls | Indexed candidate projection, O(n log n) fuel optimization, local 24-hour result cache, request throttling |
| Demonstrate with Postman and Loom | [Postman collection](postman/Fuel-Routes.postman_collection.json), [recording script](docs/loom-script.md); **the recording itself must still be made** |

**Scope limitation:** The input is a US **city/place + state**, not an arbitrary street address or GPS coordinate. The approximate `city_approx` station location is **not** a verified pump location. Cost minimization is exact only for a fixed sequence of candidates with known route positions and prices, not globally across all roads or unverified detours.

## Local demonstration setup

Bring the **original CSV supplied with the assessment**; it is intentionally excluded from Git for data rights. Use a real private HeiGIT key. Do not put keys or the price CSV in the repository or screen recording.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py import_cities
python manage.py import_census_places  # optional; needs Census network access
python manage.py import_stations /private/path/fuel-prices-for-be-assessment.csv
export ORS_API_KEY='YOUR_PRIVATE_KEY'
python manage.py check
python manage.py runserver
```

Local pages: `/` for the product introduction; `/demo/` for the actual map; `/health/` for **local data readiness only**. A key present in `/health/` is not proof the key works.

API example:

```http
POST /api/v1/routes/optimize/
Content-Type: application/json

{"start":"Chicago, IL","finish":"Denver, CO"}
```

Equivalent existing contract:

```json
{"start":{"city":"Chicago","state":"IL"},"finish":{"city":"Denver","state":"CO"}}
```

## Verification and evidence

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test routes -v 1
python -m unittest discover -s tests -v
python scripts/check_javascript.py
python scripts/run_live_checks.py
```

The first five commands run **without HeiGIT**; tests use synthetic data and mocked routing responses. The sixth must run with a working key, real imported US station data, and actual network access. It checks three cold cases: Los Angeles–Las Vegas, Chicago–Denver, and New York City–Miami, including provider-call counts and per-leg fuel accounting. Its returned errors are valid evidence of failure, not of a successful real route. Full results stay under ignored `live_results/`.

See [GitHub Actions](https://github.com/AgustinWojtyszyn/fuel-route-optimizer/actions/workflows/ci.yml) for execution status tied to the exact final commit, [OpenAPI](docs/openapi.json) for the response contract and [assessment audit](docs/assessment-2026-11-16/REPORT.md) for historical tests and documented limitations. Do not assume a passing CI workflow proves HeiGIT route connectivity.

## Must complete **before sending** to the evaluator

1. Run `scripts/run_live_checks.py` with the valid key and the source CSV; inspect real results and failures. If a route cannot be planned from approximate stations, do not substitute invented stops or statistics.
2. Open the seven Postman requests locally; verify a real short route, a longer route requiring refueling, meaningful errors and the map.
3. Record the **actual** Loom/Postman demonstration using [the recording guide](docs/loom-script.md); include the working endpoint and response, map, fuel math, API call count and limitations. Paste the **real** Loom URL in the submission message.
4. Verify that the **last** commit in `main` has passing CI, and submit its repository link. Do not share `.env`, any real API key, private input CSV or proprietary result files.

**Not yet proven by CI:** real HeiGIT routing, exact station/pump access, live station prices, live end-to-end performance, browser behavior on physical mobile devices, or existence of a Loom recording.
