"""Extract OSM fuel establishments from a downloaded Geofabrik state PBF."""

import argparse
import json

import osmium
from shapely import wkb


class ExtractFuel(osmium.SimpleHandler):
    def __init__(self, output):
        super().__init__()
        self.output = output
        self.factory = osmium.geom.WKBFactory()

    def export(self, tags, ident, point):
        if tags.get('amenity') != 'fuel':
            return
        address = ' '.join(
            item for item in (tags.get('addr:housenumber'), tags.get('addr:street')) if item
        )
        self.output.write(json.dumps({
            'source': 'OpenStreetMap', 'external_id': ident, 'license': 'ODbL-1.0',
            'url': f'https://www.openstreetmap.org/{ident}',
            'name': tags.get('name'), 'brand': tags.get('brand'), 'ref': tags.get('ref'),
            'operator': tags.get('operator'), 'address': address,
            'city': tags.get('addr:city'), 'state': tags.get('addr:state'),
            'latitude': point[1], 'longitude': point[0], 'type': 'fuel',
        }, ensure_ascii=False) + '\n')

    def node(self, node):
        if node.location.valid():
            self.export(node.tags, f'node/{node.id}', (node.location.lon, node.location.lat))

    def area(self, area):
        if area.tags.get('amenity') != 'fuel':
            return
        try:
            geom = wkb.loads(bytes.fromhex(self.factory.create_multipolygon(area)))
        except (RuntimeError, ValueError):
            return
        point = geom.representative_point()
        kind = 'way' if area.from_way() else 'relation'
        self.export(area.tags, f'{kind}/{area.orig_id()}', (point.x, point.y))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pbf')
    parser.add_argument('output')
    args = parser.parse_args()
    with open(args.output, 'w', encoding='utf-8') as stream:
        ExtractFuel(stream).apply_file(args.pbf, locations=True, idx='flex_mem')
