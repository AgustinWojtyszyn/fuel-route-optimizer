"""Reconcile operator location exports against branch IDs and Overture points."""

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from audit_station_locations import entries, inventory, normalize, write_jsonl
from corroborate_opis_locations import distance_metres

PILOT = 'https://pilotcompany.com/locations/search'
LOVES = 'https://www.loves.com/locations'
ABBREVIATIONS = {
    'street': 'st', 'road': 'rd', 'highway': 'hwy', 'avenue': 'ave',
    'drive': 'dr', 'lane': 'ln', 'boulevard': 'blvd', 'north': 'n',
    'south': 's', 'east': 'e', 'west': 'w', 'parkway': 'pkwy',
}


def street_key(text):
    return ' '.join(ABBREVIATIONS.get(word, word) for word in normalize(text).split())


def chain_name(text):
    name = normalize(text)
    if re.search(r'\b(?:pilot|flying j)\b', name):
        return 'pilot'
    if re.search(r'\blove(?:s| s)\b', name):
        return 'loves'
    return ''


def operator_stores(pilot_csv, pilot_json, loves_json):
    with pilot_csv.open(encoding='utf-8-sig', newline='') as stream:
        official = {row['Store #']: row for row in csv.DictReader(stream)
                    if row['Country'] == 'United States'}
    for branch, rec in json.loads(pilot_json.read_text()).items():
        directory = official.get(branch)
        line = next((item for item in rec['linesOfBusiness'] if item['isPrimaryLineOfBusiness']), {})
        if (not directory or rec['status'] != 'Open' or rec['state'] != directory['State']
                or street_key(rec['address1']) != street_key(directory['Address'])
                or not line.get('latitude') or not line.get('longitude')):
            continue
        yield 'pilot', branch, {
            'name': line['primaryBusinessDescription'], 'address': rec['address1'],
            'city': rec['city'], 'state': rec['state'], 'longitude': float(line['longitude']),
            'latitude': float(line['latitude']), 'source': 'Pilot Flying J official locations',
            'external_id': branch, 'url': f'https://pilotcompany.com/locations/{branch}',
            'interstate': directory['Interstate'], 'catalog_url': PILOT,
        }
    if loves_json is None:
        return
    for branch, rec in json.loads(loves_json.read_text()).items():
        if (
            rec['facilitySubtypeName'] not in {'Travel Stop', 'Country Store', 'Car Stop'}
            or rec['isOutOfNetwork'] or not rec.get('latitude') or not rec.get('longitude')
        ):
            continue
        if not isinstance(rec.get('address'), str):
            continue
        yield 'loves', branch, {
            'name': rec['preferredName'], 'address': rec['address'],
            'city': rec['city'], 'state': rec['state'], 'longitude': float(rec['longitude']),
            'latitude': float(rec['latitude']), 'source': "Love's official locations",
            'external_id': branch, 'url': f'{LOVES}/{branch}',
            'interstate': f'{rec.get("highway", "")} Exit {rec.get("exitNumber", "")}',
            'catalog_url': LOVES,
        }


def locator_key(row):
    return row['state'].upper().removeprefix('US-'), street_key(row['address'])


def run(args):
    prior = {row['opis_id']: row for row in entries(args.prior)}
    operators = {(chain, branch): row for chain, branch, row in
                 operator_stores(args.pilot_csv, args.pilot_json, args.loves_json)}
    street_keys = {locator_key(row) for row in operators.values() if row['address']}
    overture = defaultdict(dict)
    for row in entries(args.overture):
        if not row.get('state') or not row.get('address'):
            continue
        key = locator_key(row)
        if key in street_keys:
            overture[key][row['external_id']] = row
    candidates = []
    for ident, locations in inventory(args.prices).items():
        if ident in prior and prior[ident]['status'] != 'high_confidence':
            continue
        matches = {}
        for name, address, city, state in locations:
            chain = chain_name(name)
            ref = re.search(r'#\s*(\d+)\b', name)
            if not chain or not ref:
                continue
            branch = str(int(ref[1]))
            loc = operators.get((chain, branch))
            if loc and loc['state'] == state and normalize(loc['city']) == normalize(city):
                matches[(chain, branch)] = loc
        if len(matches) != 1 or len({item[3] for item in locations}) != 1:
            continue
        (chain, branch), loc = next(iter(matches.items()))
        candidates.append({'opis_id': ident, 'type': 'fuel', **loc})
        nearby = [
            row for row in overture[locator_key(loc)].values()
            if chain_name(row['name']) == chain and distance_metres(loc, row) <= 150
            and row['type'] in {'gas_station', 'truck_gas_station', 'truck_stop'}
        ]
        evidence = [{
            'url': loc['url'],
            'detail': f'Operator branch {branch}, {loc["address"]}, {loc["city"]}, {loc["state"]}.',
        }]
        status = 'high_confidence'
        reason = 'Operator branch, city and state match; independent address coordinate corroboration pending.'
        if len(nearby) == 1:
            other = nearby[0]
            status = 'verified_exact'
            reason = 'Operator branch identity and physical address corroborated by an independent fuel POI.'
            evidence.append({
                'url': other['url'],
                'detail': f'Overture {other["source_version"]}, GERS ID {other["external_id"]}, same address and brand; offset {distance_metres(loc, other):.0f} m.',
            })
        prior[ident] = {
            'opis_id': ident, 'state': loc['state'], 'status': status,
            'latitude': loc['latitude'], 'longitude': loc['longitude'],
            'source': loc['source'], 'external_id': branch,
            'verified_on': args.review_date, 'evidence': evidence,
            'road_access_verified': False, 'reason': reason,
        }
    write_jsonl(args.output, prior.values())
    write_jsonl(args.candidates, candidates)
    print(f'operator_sites={len(operators)} catalog_branch_matches={len(candidates)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('prices', 'prior', 'pilot_csv', 'pilot_json', 'overture', 'output', 'candidates'):
        parser.add_argument(field, type=Path)
    parser.add_argument('--loves-json', type=Path)
    parser.add_argument('--review-date', required=True)
    run(parser.parse_args())
