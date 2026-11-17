# US Fuel Route Planner — Django Backend Assessment

A Django 6.1.3 / Django REST Framework 3.18.3 API that plans fuel purchases along an openrouteservice driving route. SQLite stores an auditable OPIS-price catalog and an offline GeoNames city index. No commercial price file or API key is committed.

[OpenAPI 3.1 reference](docs/openapi.json) · [Postman collection](postman/Fuel-Routes.postman_collection.json) · [GitHub CI](.github/workflows/ci.yml)
[**Submission handoff and evaluator checklist**](SUBMISSION.md) — exact setup, requirements, evidence and live-demo prerequisites.


## Quick start

Python 3.12+ is recommended (developed and tested on 3.12.14).

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py import_cities
python manage.py import_census_places  # optional: expand cities with official 2026 Census places
python manage.py import_stations /private/path/fuel-prices-for-be-assessment.csv
python manage.py import_station_locations /private/path/station-locations.private.jsonl
export ORS_API_KEY='your-key-from-account.heigit.org'
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the multilingual product introduction, or `http://127.0.0.1:8000/demo/` for the responsive, accessible Leaflet route planner showing road geometry, estimated purchases, receipts and explicit station-location uncertainty. `GET /health/` checks local station/catalog readiness without contacting the provider. It reports station, city, reviewed location and legacy location counts plus whether a HeiGIT key is present (not whether that key is valid). It returns 503 if the local data cannot support route planning. `POST /api/v1/routes/optimize/` accepts city/state objects or the shorter `"City, ST"` notation (the route still uses approximate city coordinates, not arbitrary street addresses):

```json
{"start":{"city":"Chicago","state":"IL"},"finish":{"city":"Denver","state":"CO"}}
```

The equivalent compact payload is `{"start":"Chicago, IL","finish":"Denver, CO"}`. Both formats use the same local city index and do not require separate geocoding requests.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/routes/optimize/ \
  -H 'Content-Type: application/json' \
  -d '{"start":{"city":"Chicago","state":"IL"},"finish":{"city":"Denver","state":"CO"}}'
```

Import `postman/Fuel-Routes.postman_collection.json` into Postman and use its default Render URL or set `baseUrl` to your local server. Run `python manage.py test routes -v 1` for offline tests. Set `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_DEBUG=0`, `ORS_TIMEOUT_SECONDS` through the environment for deployment; `.env.example` is a reference, not loaded automatically.

## City search and expanded U.S. place coverage

The planner's origin and destination inputs have an **accessible, keyboard-operated autocomplete**. They query `GET /api/v1/cities/?q=new` (optional `&state=NY`); responses contain at most 12 existing `{name,state}` records per request. The dropdown never downloads the entire catalog or calls HeiGIT while typing. Selecting a match fills both city and state; manually typed city + two-letter state remains supported.

The base `import_cities` command uses the bundled GeoNames snapshot (population >=500; originally excludes AK and HI). This is **not every town or settlement**. To expand the searchable and routable location registry, run:

```bash
python manage.py import_census_places
# Or with an official zip you downloaded yourself:
python manage.py import_census_places --file /path/to/2026_Gaz_place_national.zip
```

This command downloads the official [2026 U.S. Census national Places gazetteer](https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html) over HTTPS (unless `--file` is supplied) and merges recognized incorporated places and Census-designated places with existing GeoNames locations **without deleting existing cities or fuel stations**. It also re-matches stations that were previously unlocated against the expanded city catalog (including on repeated imports), preserving already-located stations. Newly recovered positions remain **approximate city centers**, not verified pumps. The route cache is invalidated when station locations are recovered. It includes place candidates in Alaska and Hawaii, but a connected drivable itinerary and fuel-stop coverage there cannot be assumed. A subsequent `import_cities` refresh replaces the city table; rerun `import_census_places` afterwards to restore Census-only entries.

The Census source lists official geographic "places," not every hamlet, address or unnamed road point. All coordinates are approximate representative city/place coordinates, **not verified fuel-pump entrances**. A selectable city is not a promise of a feasible route: the 500-mile tank limit, road connectivity, routing-provider coverage and limited fuel-price CSV still apply.

The landing page at `/` introduces the assessment. The API and working planner remain at `/api/v1/routes/optimize/` and `/demo/`, respectively. Both pages support English, Spanish, French and Portuguese.

## Result contract

The result contains `route` (complete GeoJSON LineString, driving distance, duration and each verified leg length), `vehicle`, `fuel`, `stops`, and `meta`. Stops include OPIS ID, undated observed price, planned gallons and reviewed establishment coordinates labeled `verified_exact` and a separate `station_access_verified` value. `fuel.purchased_en_route_usd` is new spending; `fuel.estimated_total_trip_cost_usd` also values the initial fuel consumed, using the origin state's median price as a reference (US median fallback). These amounts are estimates in USD assuming the source prices mean USD per gallon. The vehicle starts with 50 gallons, equivalent to 500 miles at 10 mpg. Amounts remain decimal internally and monetary outputs are rounded only at presentation.

`meta.routing_api_calls` is 1 for a direct route with no purchase, 2 for a route with stops, and at most 3 to remove unused waypoints or retry an over-range detour. It is 0 for a cache hit. Successful results are cached locally for 24 hours using the price-file, location-review and city-index digests. Errors return `{"error":{"code":"...","message":"...","details":{}}}` with 400 for malformed input, 422 for unknown cities or infeasible plans, and 502/503/504 for provider failures. This development API has a basic request throttle, but no authentication or complete production deployment configuration.

## How it works

1. Import the supplied CSV locally. Exclude Canadian records; trim whitespace; group by OPIS ID; select the lower observed median price. Retain min/max, number of observations and conflict flag.
2. Import offline GeoNames cities for trip endpoints. Import the private reviewed-coordinate manifest separately for fuel stops.
3. Request direct road geometry once from `https://api.heigit.org/openrouteservice/v2/directions/driving-car/geojson`, then project verified establishments within a 12-mile corridor onto the polyline's cumulative distance.
4. On the fixed candidate order, buy only enough to reach the next strictly cheaper reachable station, otherwise enough to fill the 50-gallon tank or reach the destination. Simulate every segment and fail if any leg runs out of fuel.
5. When purchases are planned, request a waypoint route via the selected **verified establishments**. Recalculate the fuel plan using the returned road segment distances. If the road legs make the plan infeasible, try one alternative excluding the most offset station adjacent to an over-range leg. If recalculation instead leaves an unused waypoint, the final routing request removes it. Reject any itinerary that cannot be verified within that budget. The resulting route geometry is returned, with at most three provider requests.

The purchase algorithm is optimal for a fixed one-dimensional route and selected stations without access or detour penalties. It does **not** prove global optimality across alternate roads, exact station entrances, or current station availability. Check driveway access separately for each fuel stop. Routes lacking enough candidate stations return an error, never invented stops.

## Data, attribution, limits

The original assessment CSV appears to contain OPIS data. Its redistribution permission was not established, so it is excluded by `.gitignore` and the project ZIP. Obtain it from the evaluator and import locally. GeoNames city data are provided by [GeoNames](https://www.geonames.org/) under CC BY 4.0 through [geonamescache](https://github.com/yaph/geonamescache). Map data © OpenStreetMap contributors; Leaflet assets and OSM tiles load in the browser with attribution. Follow the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/) before public traffic. The routing provider is [openrouteservice / HeiGIT](https://openrouteservice.org/) and requires a free key. Its hosted driving limit is 6,000 km and 50 waypoints; quota and routing availability depend on the account. See the [final audit](docs/final-audit.md) for observed deployment results.

The pricing CSV has undated observations. The location manifest records the date and evidence for each verified coordinate. Alaska and Hawaii are outside the supplied price catalog; some itineraries crossing Canada may not be covered. Cache is per process; use shared caching for a multi-worker deployment. See `docs/verification.md` for measured results and `docs/loom-script.md` for a short demonstration script.

## Live verification and production settings

With a valid `ORS_API_KEY` in the environment, run `python scripts/run_live_checks.py`. To limit provider use to one cold case, add `--case chicago_denver`. It makes cold requests for Los Angeles→Las Vegas, Chicago→Denver, and New York City→Miami; prints HTTP status, distance, duration, stops, gallons, costs, actual provider request count and wall times, and checks the tank against each returned leg. Full JSON results are saved under ignored `live_results/` for private review. Do not publish these derived OPIS prices without permission. Without the key, the script exits before any external request.

The HeiGIT key's validity has not been verified here; use the actual key issued by your account through a private environment variable. No external provider result has been assumed or invented. For deployment, set `DJANGO_DEBUG=0`, a long random `DJANGO_SECRET_KEY`, allowed hosts, and HTTPS. Production settings enable secure cookies, redirect and HSTS. If behind a trusted TLS reverse proxy, configure its forwarded scheme securely before enabling redirect. The API includes a basic per-client throttle but no authentication or distributed quota enforcement; do not expose it publicly without shared caching, abuse protection and deployment review.


## Quality gates and financial precision (November 2026 update)

GitHub Actions runs the Django integration tests, a separate standard-library test suite, Python compilation and a migration check for **Python 3.12 and 3.13** on every push to `main`. The independent suite includes 1,000 deterministic random cases checked against exhaustive integer-gallon dynamic programming, 7,000-station scalability coverage, and deliberate accounting failures. Run locally:

```bash
python -m unittest discover -s tests -v
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test routes -v 1
```

For small fractional purchases, the API now preserves exact decimal gallons instead of rounding to four places. Each stop exposes `fuel_before_stop_gallons` and `fuel_after_stop_gallons`; station charges round independently to cents, and `purchased_en_route_usd` exactly equals the sum of these displayed receipts. `initial_fuel_estimated_cost_usd` separates the **notional** cost of fuel already in the tank from money spent at new stops. API cache keys were incremented to avoid returning stale response formats. Only reviewed physical station records are eligible for recommendations. Driveway access is tracked independently.

`python scripts/run_live_checks.py` requires a real HeiGIT key, validates every returned road segment, reconciles all gallons/cents and provider calls, continues after a failed route, and **exits nonzero if any check fails**. Do not use local mocked tests as evidence of real provider availability or driving feasibility.

Sources: [Django security releases](https://www.djangoproject.com/weblog/2026/nov/03/security-releases/), [DRF 3.18.3](https://www.django-rest-framework.org/community/release-notes/), [openrouteservice return formats](https://github.com/GIScience/openrouteservice/blob/main/docs/api-reference/endpoints/directions/requests-and-return-types.md), [hosted limits](https://giscience.github.io/openrouteservice/hosted-api-restrictions).

## Operational safety

The optimization endpoint applies a configurable, per-IP Django REST Framework throttle
(default `120/min`; `DJANGO_ROUTE_RATE` overrides it). Throttled calls return HTTP 429
with the same `error.code=rate_limited` envelope as other API errors. This is a
single-process development safeguard; configure shared caches, reverse-proxy rules,
authentication and abuse controls before exposing a multi-worker public API.
The fuel verifier rejects **any** deficit, including below 0.00000001 gallons;
route legs and required gallons are returned at sufficient precision to replay
the calculation independently.

[![Python API checks](https://github.com/AgustinWojtyszyn/fuel-route-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/AgustinWojtyszyn/fuel-route-optimizer/actions/workflows/ci.yml)

## Verified continuous-integration evidence

GitHub Actions has confirmed the independent optimizer/verification suite and Django
integration suite on Python 3.12 and 3.13, using mocked provider responses:
[latest workflow history](https://github.com/AgustinWojtyszyn/fuel-route-optimizer/actions/workflows/ci.yml).
That is **not** an end-to-end HeiGIT check; the real provider, current fuel prices,
station-entrance coordinates, and driving route availability remain unverified.
The code fails closed when a waypoint route cannot be validated. The validation
also rejects degenerate provider geometry instead of exposing an HTTP 500.

The readiness endpoint intentionally does not call HeiGIT or claim provider connectivity; use the live route verification script for that. Import both cities and station data before accepting a `200` on `/health/`.

## Dataset preflight and import safety (November 2026)

Before requesting any paid/quota-limited routing-provider operation, the optimize
endpoint checks that the local US station catalog is populated and that at least
one station has a verified establishment location. Missing data returns HTTP 422 with
`error.code=empty_catalog` or `error.code=station_locations_missing`, with
**zero requests to HeiGIT**. The `/health/` endpoint remains the local readiness
check and does not authenticate with the provider.

The CSV importer validates OPIS/rack identifiers, text-field lengths, finite
prices and database-storable decimal precision before replacing existing rows.
A rejected import leaves the previous station catalog and dataset digest
untouched. Neither check turns city centroids into verified truckstop locations:
pump access and actual ORS route results still require independent verification.

## Final assessment — 16 November 2026

The [current A–G assessment report](docs/assessment-2026-11-16/REPORT.md) records the starting revision, demonstrated defects, corrections, raw test results, independent reviews and remaining external checks. Older reports under `docs/redesign/` and `docs/verification.md` are historical evidence, not results for the current UI.

The current local suites pass **57 Django tests and 30 independent tests**, including **1,750 deterministic comparisons against an exhaustive optimizer**. UI regression tests reproduce and protect translated API errors, preserved error state, translated warnings, invalidation of old results and valid US state codes. English and dark mode are the defaults; manual language/theme preferences persist across both pages. The landing schematic is conceptual and does not represent a real road or verified pump.

Browser validation covers **320×720, 375×812, 430×932, 768×1024, 1280×800, 1440×900 and 1920×1080**, four locales and both themes. The new matrix passed **629 assertions in 112 states**; the six focused UI regressions and the original 138 browser assertions also passed. This is desktop Chrome automation at the stated viewport sizes, not a physical-device or Safari certification.

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test -v 1
python -m unittest discover -s tests -v
python scripts/check_javascript.py
node --check routes/static/routes/landing.js
node --check routes/static/routes/theme.js
# Optional browser tooling, outside project/runtime dependencies:
npm install --prefix /tmp/fuel-browser puppeteer@24.43.1
# Start Django on 127.0.0.1:8134 in another terminal first.
FUEL_BROWSER_MODULE=/tmp/fuel-browser/node_modules/puppeteer node scripts/test_assessment.cjs
FUEL_BROWSER_MODULE=/tmp/fuel-browser/node_modules/puppeteer node scripts/test_ui_regressions.cjs
```

`python manage.py collectstatic --noinput` prepares the UI assets under ignored `staticfiles/`; a deployment must serve that directory through its own static server. This does not configure or deploy production hosting.

Import the three [Postman requests](postman/Fuel-Routes.postman_collection.json) for the deployed demonstration. The [Loom recording guide](docs/loom-script.md) gives the screen order and English narration.

See [reviewed station imports and Render startup](docs/station-location-rollout.md) for the location manifest and repeatable recovery procedure.
