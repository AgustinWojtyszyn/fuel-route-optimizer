"""Convert a filtered Overture Places export into auditable station candidates."""
import argparse
import json
from pathlib import Path


def normalize(path, version):
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            place = json.loads(line)
            ident = place['id']
            provenance = place.get('sources') or []
            for address in place.get('addresses') or []:
                if address.get('country') != 'US':
                    continue
                yield {
                    'source': 'Overture Maps Places', 'source_version': version,
                    'external_id': ident, 'name': place['name'],
                    'address': address.get('freeform'), 'city': address.get('locality'),
                    'state': address.get('region'), 'type': place['category'],
                    'latitude': place['latitude'], 'longitude': place['longitude'],
                    'confidence': place.get('confidence'),
                    'websites': place.get('websites') or [],
                    'url': f'https://explore.overturemaps.org/#map=18/{place["latitude"]}/{place["longitude"]}',
                    'license': sorted({item['license'] for item in provenance if item.get('license')}),
                    'provenance': provenance,
                }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version')
    parser.add_argument('files', nargs='+', type=Path)
    args = parser.parse_args()
    for path in args.files:
        for row in normalize(path, args.version):
            print(json.dumps(row, ensure_ascii=False, separators=(',', ':')))
