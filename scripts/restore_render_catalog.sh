#!/usr/bin/env bash
set -euo pipefail

price_file=${FUEL_PRICE_FILE:-/etc/secrets/fuel-prices-for-be-assessment.csv}
location_file=${FUEL_LOCATION_FILE:-/etc/secrets/station-locations.private.jsonl.gz.b64}
minimum_verified=${FUEL_MIN_VERIFIED_STATIONS:-6626}

if [[ ! -s "$price_file" || ! -s "$location_file" ]]; then
    echo "Required private fuel catalog file is missing or empty." >&2
    exit 1
fi

python manage.py migrate --noinput
python manage.py import_cities
python manage.py import_stations "$price_file"
python manage.py import_station_locations "$location_file" --min-verified "$minimum_verified"
