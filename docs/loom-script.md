# Loom demo outline (maximum 4:45)

- 0:00–0:30: Show Django/DRF project, original CSV kept outside Git and 6,626 imported US stations.
- 0:30–1:25: In Postman, run a live long-route example with your own HeiGIT key. Point out distance, complete GeoJSON, stops, gallons, new spending and estimated consumption cost. Only state real numbers observed during recording.
- 1:25–2:10: Open `/demo/`, draw the returned route and approximate city markers. State the station-coordinate limitation.
- 2:10–2:50: Run a short route, then an invalid city or infeasible route to show controlled errors.
- 2:50–4:05: Show `fuel_optimizer.py`, `routing_client.py`, import command and the one/two-call behavior.
- 4:05–4:45: Run `python manage.py test routes`, show 20 passing tests and show live route measurements after loading a valid key.
