# Record the Fuel Route Optimizer demo

Target length is **4 minutes**. The recording uses the deployed API and does not need a local key.

## Set up your screen

1. Open the [landing page](https://fuel-route-optimizer-dyth.onrender.com/), the [planner](https://fuel-route-optimizer-dyth.onrender.com/demo/), and [GitHub Actions](https://github.com/AgustinWojtyszyn/fuel-route-optimizer/actions).
2. Import [Fuel-Routes.postman_collection.json](../postman/Fuel-Routes.postman_collection.json) in Postman. Its default base URL is Render. All three requests use `POST /api/v1/routes/optimize/` with JSON and require no client credentials.
3. Send the short and long requests before recording to verify today's provider availability. Open the planner and calculate **Chicago → Denver**. Expand **Recommended fuel stops**. Keep your CSV, secrets and Render environment settings out of the recording.
4. To display test output locally, run `python manage.py test routes -v 1` and `python -m unittest discover -s tests -v` after installing the pinned requirements. For a cold local provider check with private data and a valid key, run `python scripts/run_live_checks.py --case chicago_denver`. The live check saves full responses privately and counts actual outgoing provider requests.

## 0:00–0:35 · Landing page and architecture

“Hi, I’m Agustín. This is Fuel Route Optimizer, a Django REST Framework API for planning fuel purchases between U.S. cities. Django validates the city and state against a local catalog. openrouteservice supplies the road geometry, and the planner uses prices from the assessment CSV. The vehicle starts with 50 gallons. At 10 miles per gallon, that gives it a maximum range of 500 miles.”

## 0:35–1:20 · Short route in Postman

Send **Short | Los Angeles to Las Vegas**. Collapse `route.geometry.coordinates` after showing the GeoJSON type. Expand `vehicle`, `fuel`, and `meta`.

“This is the road route as a GeoJSON LineString. For this trip, the starting tank covers the whole distance, so the API recommends no stops. The JSON separates the estimated value of the fuel already in the tank from money spent along the way.”

## 1:20–2:35 · Long route in Postman

Send **Long | Chicago to Denver**. Expand one entry in `stops` and show the leg distances and totals.

“For a longer trip, the planner projects reviewed stations onto the first route. On that fixed sequence, it looks for the next cheaper station it can reach and buys enough to get there. Otherwise it buys up to the tank limit or the amount needed to reach the destination. A waypoint request gives us the actual road legs through the chosen locations. The API recalculates the purchases and checks how much fuel is left after each leg. It can try one alternative if a road leg exceeds the range or the provider routes too far from a stop. The selected roads and station coverage limit the search.”

“Here are the gallons bought, the per-stop costs and the sum of new purchases. The estimated total adds a reference value for fuel consumed from the starting tank. On an uncached request, we use one routing call for a direct trip or up to three for a trip with stops. A cache hit reports zero new calls.”

## 2:35–3:20 · Map and costs

Switch to the prepared planner tab. Show the route line, click a numbered marker, and point to the cost breakdown.

“The map uses the same geometry and station locations as the API response. Each stop shows the site, gallons to buy, price per gallon, and estimated cost. Station locations were reviewed. Driveway access is flagged separately, and price observations are undated.”

## 3:20–4:00 · Error, tests, and close

Send **Invalid | Unknown US city and state pair**. Expand `error`, then show passing tests for the commit you are presenting.

“This invalid city and state return a structured 422 before the API contacts the router. Automated tests cover fuel accounting, provider failures and a detour that would exceed the vehicle’s range. The repository includes the API contract and the Postman collection. Thanks for watching.”
