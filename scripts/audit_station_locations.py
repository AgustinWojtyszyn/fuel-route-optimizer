"""Build a private audit inventory and runtime manifest without exposing prices."""

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

US_STATES = frozenset(
    'AL AZ AR CA CO CT DE FL GA HI IA ID IL IN KS KY LA MA MD ME MI MN MO MS MT NC ND NE '
    'NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY'.split()
) - {'HI'}


def normalize(text):
    folded = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', ' ', folded.casefold()).strip()


def inventory(path):
    grouped = defaultdict(set)
    with path.open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream):
            ident, name, address, city, state = (
                row[key].strip() for key in ('OPIS Truckstop ID', 'Truckstop Name', 'Address', 'City', 'State')
            )
            if state.upper() in US_STATES:
                grouped[ident].add((name, address, city, state.upper()))
    return grouped


def entries(path):
    with path.open(encoding='utf-8-sig') as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path, rows):
    with path.open('w', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')


def audit(prices, review_files, candidate_files, output):
    records = inventory(prices)
    reviewed = {}
    candidates = defaultdict(list)
    by_name = defaultdict(list)
    by_address = defaultdict(list)
    for path in review_files:
        for row in entries(path):
            ident = row['opis_id']
            if ident not in records or ident in reviewed:
                raise ValueError('Unknown or duplicate reviewed OPIS ID.')
            if row['state'] not in {item[3] for item in records[ident]}:
                raise ValueError('Review state differs from the source record.')
            reviewed[ident] = row
    for path in candidate_files:
        for row in entries(path):
            if row.get('opis_id') in records:
                candidates[row['opis_id']].append(row)
            if row.get('state'):
                region = row['state'].upper().removeprefix('US-')
                city = normalize(row.get('city'))
                by_name[(region, city, normalize(row.get('name')))].append(row)
                if row.get('address'):
                    by_address[(region, city, normalize(row['address']))].append(row)
    report = []
    for ident, alternatives in sorted(records.items()):
        plausible = {}
        for match in candidates[ident]:
            plausible[(match['source'], match['external_id'])] = match
        for name, address, city, state in alternatives:
            for match in by_name[(state, normalize(city), normalize(name))] + by_address[
                (state, normalize(city), normalize(address))
            ]:
                plausible[(match['source'], match['external_id'])] = match
        name, address, city, state = min(alternatives)
        if ident in reviewed:
            result = reviewed[ident]
        else:
            result = {
                'opis_id': ident, 'state': state, 'status': 'ambiguous' if len(plausible) > 1 else 'unlocated',
                'reason': 'Independent establishment and coordinate evidence pending.',
            }
        report.append({
            'name': name, 'original_address': address, 'city': city,
            'identity_conflicts': sorted(alternatives) if len(alternatives) > 1 else [],
            'candidates': list(plausible.values()), **result,
        })
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / 'station-audit.private.jsonl', report)
    write_jsonl(output / 'station-pending.private.jsonl', (
        row for row in report if row['status'] != 'verified_exact'
    ))
    write_jsonl(output / 'station-locations.private.jsonl', reviewed.values())
    counts = Counter(row['status'] for row in report)
    print(json.dumps({
        'catalog': len(records), 'price_file_sha256': hashlib.sha256(prices.read_bytes()).hexdigest(),
        **{key: counts[key] for key in ('verified_exact', 'high_confidence', 'ambiguous', 'unlocated')},
        'ids_with_candidates': sum(bool(row['candidates']) for row in report),
    }))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prices', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--reviewed', type=Path, action='append', default=[])
    parser.add_argument('--candidates', type=Path, action='append', default=[])
    args = parser.parse_args()
    audit(args.prices, args.reviewed, args.candidates, args.output)
