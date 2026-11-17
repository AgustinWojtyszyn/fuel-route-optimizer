# Reviewed fuel-station locations

The price import retains original OPIS IDs as text and preserves existing
location reviews when station identity is unchanged. GeoNames and Census imports
serve place search. The planner projects only reviewed physical establishments
onto route geometry. Station coordinates and driveway access have separate
evidence requirements. A changed review invalidates the route cache.

Use a private JSONL file with one record per reviewed ID. Required fields are
`opis_id`, `state` and `status`. Verified records also require latitude,
longitude, source, external ID, review date (`verified_on`), and at least two
independent HTTPS evidence entries with a URL and a short detail. Evidence
for driveway access must include `kind: "road_access"` before setting
`road_access_verified`. Review artifacts remain outside version control.
Address or name similarity generates a candidate for review.

Use `scripts/audit_station_locations.py` to generate the private per-ID reports
from the original CSV, normalized geographic candidates and reviewed JSONL
records. It emits only an aggregate summary to stdout. `normalize_overture_fuel.py`
and `extract_osm_fuel.py` convert Overture and Geofabrik extracts into candidates.
Record upstream release versions and licenses with the evidence. OpenStreetMap
data is ODbL and any distribution of derived data must comply with that license.

## Repeatable Render Free startup

Render Free uses ephemeral storage. Both the existing private price CSV and the
reviewed-coordinate manifest must be present on every cold start. Render serves
secret files from `/etc/secrets` and limits their combined size to 1 MB. Check the
size before upload. Render accepts the reviewed manifest as a private text file
named `station-locations.private.jsonl.gz.b64`, containing the Base64 encoding
of the gzipped JSONL. Larger reviewed files may require an authorized private
download or a redistributable upstream artifact with a configured checksum.
The repository must never carry the original commercial price CSV.

After configuring both files, run the recovery script from the app directory
before starting Gunicorn. The existing Render build command collects static files and generates `render_wsgi.py` as a WhiteNoise wrapper for `config.wsgi`. The start command then uses the configured port and coverage floor.

```bash
FUEL_MIN_VERIFIED_STATIONS=456 bash scripts/restore_render_catalog.sh &&
  gunicorn render_wsgi:application --bind "0.0.0.0:$PORT" --workers 1 --timeout 90
```

The script requires 6,626 verified stations by default. An explicitly supplied
`FUEL_MIN_VERIFIED_STATIONS` can set the validated coverage floor for a staged
rollout. Verify coverage and route feasibility before selecting a lower floor.
After startup, confirm the verified and total counts at `/health/`, repeat from
a fresh SQLite database, and check an actual route whose fuel stops appear in
the reviewed manifest.

## Geographic sources

- US Census 2024 cartographic boundaries, 1:5,000,000. State polygons were
  converted to WGS84 GeoJSON, rounded to six decimal places and gzip-compressed.
  The baseline is conservative near simplified state borders.
  https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_5m.zip
- Overture Maps Places schema and source provenance.
  https://docs.overturemaps.org/guides/places/
- OpenStreetMap data via per-state Geofabrik downloads.
  https://download.geofabrik.de/north-america/us.html
- OPIS Truckstop Spread Report public sample and product information.
  https://www.opis.com/product/pricing/retail-fuel-prices/truckstop-spread-report/
