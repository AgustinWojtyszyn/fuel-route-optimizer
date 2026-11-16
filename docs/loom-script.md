# Loom video: authentic 4–5-minute technical walkthrough

**Do not record fabricated live results.** Verify the actual route, current import, and
provider key before recording. If HeiGIT is inaccessible, state that explicitly and
show mocked tests as mocked. Do not screen-share secrets or the proprietary CSV.

- **0:00–0:35:** Introduce the Django REST Framework API and project structure.
  Show a green GitHub Actions check on Python 3.12 and 3.13.
- **0:35–1:20:** Use Postman to POST a short US route, with a genuinely working
  HeiGIT key. Explain return geometry, segment distances and the 500-mile tank.
- **1:20–2:10:** POST a longer route. Show actual recorded stops, gallons,
  station receipts, notional cost of the starting fuel and the separate amount
  spent en route. Only state actual numbers obtained during the recording.
- **2:10–2:50:** Open `/demo/` to show the returned road geometry and each
  approximate marker. Explain **city center is not an actual verified gas pump**.
- **2:50–3:25:** Show a controlled 400/422 error for bad input and the `/health/`
  local catalog-readiness response. Key presence alone does not prove connectivity.
- **3:25–4:20:** Explain `fuel_optimizer.py`, the offline synthetic exhaustive
  test, and typically one or two provider calls (at most three).
- **4:20–4:45:** Close with `python manage.py test routes` and the live check
  results if actual requests succeeded. Show README and OpenAPI for reproducibility.

**Delivery:** share the GitHub repository and Loom URL. Keep the source price file,
any HeiGIT key and live derived OPIS outputs private.
