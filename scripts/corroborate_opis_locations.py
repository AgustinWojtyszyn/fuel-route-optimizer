"""Corroborate OPIS sample records with independently sourced place coordinates."""

import argparse
import math
from collections import defaultdict
from pathlib import Path

from audit_station_locations import entries, normalize, write_jsonl


def key(row):
    name = normalize(row.get('name'))
    street = normalize(row.get('address'))
    city = normalize(row.get('city'))
    state = (row.get('state') or '').upper().removeprefix('US-')
    return (name, street, city, state) if all((name, street, city, state)) else None


def distance_metres(left, right):
    lat = (left['latitude'] + right['latitude']) / 2
    dy = 111_195 * (left['latitude'] - right['latitude'])
    dx = 111_195 * math.cos(math.radians(lat)) * (left['longitude'] - right['longitude'])
    return math.hypot(dx, dy)


def corroborate(reviews, opis_places, overture_places):
    opis = {row['opis_id']: row for row in opis_places}
    keys = {key(row) for row in opis.values()} - {None}
    places = defaultdict(dict)
    for row in overture_places:
        identity = key(row)
        if identity in keys and row['type'] in {'gas_station', 'truck_gas_station', 'truck_stop'}:
            places[identity][row['external_id']] = row
    for review in reviews:
        record = opis.get(review['opis_id'])
        if record is None or review['status'] == 'verified_exact':
            yield review
            continue
        matches = list(places[key(record)].values())
        if len(matches) == 1 and (distance := distance_metres(record, matches[0])) <= 100:
            candidate = matches[0]
            yield {
                **review, 'status': 'verified_exact',
                'reason': f'OPIS ID and identical independent establishment name/address. Points differ by {distance:.0f} m.',
                'evidence': [
                    *review['evidence'], {
                        'url': candidate['url'],
                        'detail': f'Overture {candidate["source_version"]}, GERS ID {candidate["external_id"]}, corroborates the name, street and location.',
                    },
                ],
            }
        else:
            yield review


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review', type=Path)
    parser.add_argument('opis', type=Path)
    parser.add_argument('overture', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    write_jsonl(args.output, corroborate(entries(args.review), entries(args.opis), entries(args.overture)))
