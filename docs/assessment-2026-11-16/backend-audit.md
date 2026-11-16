# Independent backend assessment audit — 2026-11-16

Baseline reviewed: `7d6633a`; source discovered through codebase-memory MCP, then current source inspected. Initial suites passed: 21 independent tests and 53 Django tests. No P0/P1 mathematical defect was demonstrated.

## Demonstrated defects (P2; corrected only after failing regression tests)

1. `routes/services/routing_client.py:58`: Python coerces JSON booleans through `float(True)`. The boundary accepted `true` as a segment distance, summary distance or duration. It also accepted a zero summary when a small positive segment fell within the existing 0.1-mile summary tolerance. New tests reproduced all four cases; they now fail closed as existing `routing_response` / HTTP 502. Numeric shape support, endpoint, successful response contract and provider request count were not changed.
2. `scripts/verification.py:40`: purely internal reconciliation accepted a different vehicle (20 MPG, 100-gallon capacity, a balanced 49-gallon initial tank, or explicit range 1,000 miles). New tests reproduced acceptance before correction. Verification now enforces 10 MPG, 50-gallon capacity, a full 50-gallon start, and explicit range 500 when supplied. Older minimal unit fixtures without the redundant `max_range_miles` key remain supported; MPG × capacity still implies exactly 500 miles. Original tests were not changed.

The new suite initially produced eight failures, across six failing methods and boolean subcases, with the three optimizer tests already passing. After the fixes, all pass.

## Mathematical review

- `fuel_optimizer.py` retained unchanged: fixed maximum 50 gallons, 10 MPG, 500-mile range; finite/nonnegative input checks, no negative fuel, no overfill, deterministic co-located cheapest station identity, strict next-cheaper reachability and exact Decimal purchase quantities.
- New `tests/test_assessment_audit.py`: 750 deterministic cases with fractional 0.1-gallon purchases, partial initial tanks and decimal prices compared against an independent exhaustive DP over all 501 tank levels (capacity measured in one-mile/0.1-gallon units). The DP enumerates every departure level with a prefix minimum of every valid arrival; it uses no greedy station selection. All exact costs match, or both implementations declare infeasibility.
- Existing independent tests retain 1,000 integer-gallon exhaustive comparisons; combined differential coverage is 1,750 synthetic cases. Added exact 500-mile boundaries, equal prices and an inaccessible cheaper offer requiring an expensive intervening stop.
- `route_planner.py` retained unchanged: road-waypoint route is reoptimized using returned leg lengths; no successful route is emitted if a verified leg cannot be traveled, or a final waypoint-removal plan remains unstable.
- New `routes/tests/test_assessment_contract.py`: actual API result envelopes generated with explicitly mocked road routes and synthetic database records are replayed through `verify_plan`. Covers no purchases with one provider call, multiple purchases with two calls, waypoint removal with three calls, and a 501-mile verified segment returning controlled 422. Purchases reconcile to per-stop receipts, all stops retain `city_approx` and `station_access_verified=False`.
- `ROUND_HALF_UP` individual station receipts reconcile to the reported purchase sum. Initial consumed fuel is valued separately from new purchases; it is `min(consumed,50) * reference_price`, not always the price of all 50 starting gallons.
- Provider errors retain sanitized, controlled codes for key/quota rejection, malformed data, timeout and connectivity. Geometry coordinate validation and handling of 2D/3D GeoJSON remain unchanged.
- `run_live_checks.py` retained unchanged. It counts actual outgoing provider requests, clears cache, verifies each returned leg/receipt, saves detailed outputs privately, continues after an unsuccessful case, and exits nonzero if any route is unsuccessful. No live call was made by this audit task.

## Performance evidence

Five local CPU-only executions of the fixed-sequence optimizer on 7,000 synthetic offers and 7,100 miles took 0.017829, 0.018995, 0.017139, 0.020208 and 0.031919 seconds. No network or database work is included. This stress case purchases at 6,600 increasingly priced offers; it is not a feasible public-API waypoint itinerary or an end-to-end response-time claim. The public API explicitly rejects more than 48 selected stops because the provider has a 50-waypoint limit.

## Results and files

- `.venv/bin/python -m unittest discover -s tests -v`: **30/30 passed**, 0.488 s in the final run (including the nine new methods).
- `.venv/bin/python manage.py test routes -v 1`: **57/57 passed**, 0.121 s in the final complete run (including four new contract methods; UI team may add more later).
- `.venv/bin/python -O -m unittest discover -s tests -q`: **30/30 passed**, 0.511 s; independent verifier conditions remain active under optimized Python.
- `.venv/bin/python manage.py test routes.tests.test_assessment_contract -v 0`: **4/4 passed**, 0.023 s after simplifying test setup.
- `git diff --check`: passed at audit completion.

Changed files: `routes/services/routing_client.py`, `scripts/verification.py`. New tests: `tests/test_assessment_audit.py`, `routes/tests/test_assessment_contract.py`. No existing test, optimizer decision, API envelope, endpoint, schema, migration, CSV, key or data record was changed. No commit made by this agent.

Raw local logs: `/tmp/fuel-backend-independent.txt`, `/tmp/fuel-backend-django.txt`, `/tmp/fuel-backend-optimized-python.txt`.

## Limits

This proves behavior on fixed station sequences and synthetic mocked provider contracts, not global optimality across roads, live HeiGIT access, live fuel prices, real station entrances or actual trip feasibility. Approximate city centers remain approximate and unverified. The candidate corridor, provider waypoint cap and possible route infeasibility remain explicit constraints.
