import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from rest_framework.test import APIClient

from routes.models import City, DatasetState, Station, StationLocation
from routes.services.station_matching import candidates

HEADER = 'OPIS Truckstop ID,Truckstop Name,Address,City,State,Rack ID,Retail Price\n'
OASIS_REFERENCE = 'https://www.wilmapco.org/freight/Truck_Flyer_2024.pdf'
OPIS_REFERENCE = 'https://info.opisnet.com/'


class StationLocationTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.prices = Path(self.tmp.name, 'prices.csv')
        self.manifest = Path(self.tmp.name, 'locations.jsonl')
        City.objects.create(name='Laurel', state='DE', latitude=38.5565, longitude=-75.5717)
        self.write_prices('3.11223344')
        call_command('import_stations', str(self.prices))
        self.oasis = {
            'opis_id': '00077', 'state': 'DE', 'status': 'verified_exact',
            'latitude': 38.560514, 'longitude': -75.556106,
            'source': 'OPIS', 'external_id': '00077', 'verified_on': '2026-11-17',
            'evidence': [
                {'url': OPIS_REFERENCE, 'detail': 'Public sample lists ID and facility coordinates.'},
                {'url': OASIS_REFERENCE, 'detail': 'Regional source identifies the same facility address.'},
            ],
        }

    def write_prices(self, price):
        self.prices.write_text(
            HEADER + f'00077,Oasis Travel Plaza,30759 Sussex Hwy,Laurel,DE,1,{price}\n'
            '52548,Henderson Fuel Mart,I-80 EXIT 342,Henderson,NE,1,2.90\n'
            '00078,Synthetic neighbor,Test address,Laurel,DE,1,3.00\n',
            encoding='utf-8',
        )

    def load(self, *rows, **options):
        self.manifest.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
        call_command('import_station_locations', str(self.manifest), **options)

    def test_reimports_preserve_verified_geometry_id_and_price_precision(self):
        self.load(self.oasis)
        self.write_prices('3.55667788')
        call_command('import_stations', str(self.prices))
        call_command('import_cities')
        station = Station.objects.get(pk='00077')
        self.assertEqual(str(station.price), '3.55667788')
        self.assertEqual(station.reviewed_location.longitude, -75.556106)
        self.assertEqual(station.reviewed_location.external_id, '00077')
        self.assertEqual(Station.objects.count(), 3)

    def test_invalid_reviews_are_atomic(self):
        self.load(self.oasis)
        digest = DatasetState.objects.get(pk='station_locations').digest
        wrong = (
            {**self.oasis, 'latitude': 38.5565, 'longitude': -75.5717},
            {**self.oasis, 'latitude': 40.780250, 'longitude': -97.812209},
            {**self.oasis, 'evidence': self.oasis['evidence'][:1]},
            {**self.oasis, 'opis_id': '77'},
        )
        for row in wrong:
            with self.subTest(row=row), self.assertRaises(CommandError):
                self.load(row)
        with self.assertRaises(CommandError):
            self.load(self.oasis, {**self.oasis, 'opis_id': '00078'})
        with self.assertRaises(CommandError):
            self.load(self.oasis, min_verified=3)
        self.assertEqual(DatasetState.objects.get(pk='station_locations').digest, digest)
        self.assertEqual(StationLocation.objects.count(), 1)

    def test_unverified_locations_are_excluded_and_check_mode_does_not_write(self):
        City.objects.create(name='Henderson', state='NE', latitude=40.780250, longitude=-97.812209)
        call_command('import_stations', str(self.prices))
        line = {'geometry': {'coordinates': [[-98.0, 40.78], [-97.5, 40.78]]}, 'distance_miles': 26}
        henderson = {
            'opis_id': '52548', 'state': 'NE', 'status': 'ambiguous',
            'latitude': 40.780250, 'longitude': -97.812209,
        }
        self.load(self.oasis, henderson, check=True)
        self.assertFalse(StationLocation.objects.exists())
        self.load(self.oasis, henderson)
        self.assertEqual(candidates(line), [])
        toward_oasis = {
            'geometry': {'coordinates': [[-75.55, 38.50], [-75.55, 38.65]]},
            'distance_miles': 12,
        }
        self.assertEqual([station.pk for _, station, _ in candidates(toward_oasis)], ['00077'])

    @patch('routes.views.plan', return_value={'meta': {}})
    def test_changed_coordinate_manifest_invalidates_route_cache(self, plan):
        cache.clear()
        self.addCleanup(cache.clear)
        self.load(self.oasis)
        client = APIClient()
        body = {'start': 'Laurel, DE', 'finish': 'Dover, DE'}
        for _ in range(2):
            self.assertEqual(client.post('/api/v1/routes/optimize/', body, format='json').status_code, 200)
        self.assertEqual(plan.call_count, 1)
        self.load({**self.oasis, 'longitude': -75.556114})
        self.assertEqual(client.post('/api/v1/routes/optimize/', body, format='json').status_code, 200)
        self.assertEqual(plan.call_count, 2)


class FuelStopRoutingGeometryTests(TestCase):
    @patch.dict('os.environ', {'ORS_API_KEY': 'test-key'})
    @patch('routes.services.routing_client.httpx.post')
    def test_far_snap_is_not_accepted_as_station_access(self, post):
        from routes.services.routing_client import RoutingError, get_route
        post.return_value.status_code = 200
        post.return_value.json.return_value = {'features': [{
            'geometry': {
                'type': 'LineString',
                'coordinates': [[-75.6, 38.7], [-75.55, 38.57], [-75.5, 38.4]],
            },
            'properties': {'way_points': [0, 1, 2],
                           'segments': [{'distance': 15000}, {'distance': 20000}],
                           'summary': {'distance': 35000, 'duration': 2000}},
        }]}
        points = [[-75.6, 38.7], [-75.55, 38.57], [-75.5, 38.4]]
        self.assertEqual(len(get_route(points)['legs_miles']), 2)
        points[1] = [-75.55, 38.59]
        with self.assertRaises(RoutingError) as caught:
            get_route(points)
        self.assertEqual(caught.exception.code, 'station_route_access')
