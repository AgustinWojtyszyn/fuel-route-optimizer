"""Import readiness and protection against incomplete or malformed price data."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from rest_framework.test import APIClient

from routes.models import City, DatasetState, Station


def station(ident='seed', *, located=False):
    return Station.objects.create(
        opis_id=ident, name='Original', address='Exit 1', city='Origin',
        state='IL', rack_id='3', price='3.00',
        price_min='3.00', price_max='3.00',
        price_observations=1, price_conflict=False,
        latitude=40 if located else None,
        longitude=-100 if located else None,
        location_quality='city_approx' if located else 'unlocated',
    )


class CatalogPreflightTests(TestCase):
    def setUp(self):
        City.objects.create(name='Origin', state='IL', latitude=40, longitude=-100)
        City.objects.create(name='Target', state='IL', latitude=40, longitude=-90)
        self.client = APIClient()
        self.request = {
            'start': {'city': 'Origin', 'state': 'IL'},
            'finish': {'city': 'Target', 'state': 'IL'},
        }

    @patch('routes.services.route_planner.get_route')
    def test_empty_catalog_rejected_without_provider_request(self, provider):
        response = self.client.post('/api/v1/routes/optimize/', self.request, format='json')
        self.assertEqual(response.status_code, 422, response.content)
        self.assertEqual(response.data['error']['code'], 'empty_catalog')
        provider.assert_not_called()

    @patch('routes.services.route_planner.get_route')
    def test_unlocated_catalog_rejected_without_provider_request(self, provider):
        station()
        response = self.client.post('/api/v1/routes/optimize/', self.request, format='json')
        self.assertEqual(response.status_code, 422, response.content)
        self.assertEqual(response.data['error']['code'], 'station_locations_missing')
        provider.assert_not_called()


class ImportSafetyTests(TestCase):
    HEADER = 'OPIS Truckstop ID,Truckstop Name,Address,City,State,Rack ID,Retail Price\n'

    def setUp(self):
        station()
        DatasetState.objects.create(key='stations', digest='existing-version')

    def test_invalid_csv_preserves_catalog_and_dataset_version(self):
        invalid_rows = (
            '2,Alpha,Exit,Origin,IL,1,3.123456789',
            '2,Alpha,Exit,Origin,IL,1,10000.00',
            '2,Alpha,Exit,Origin,IL,1,NaN',
            '2,' + 'x' * 201 + ',Exit,Origin,IL,1,3.00',
            '9' * 33 + ',Alpha,Exit,Origin,IL,1,3.00',
            '2,Alpha,Exit,Origin,IL,' + '9' * 33 + ',3.00',
        )
        with TemporaryDirectory() as directory:
            file = Path(directory) / 'stations.csv'
            for bad in invalid_rows:
                with self.subTest(bad=bad[:50]):
                    file.write_text(
                        self.HEADER +
                        '1,Good,Exit,Origin,IL,1,3.50\n' + bad + '\n',
                        encoding='utf-8',
                    )
                    with self.assertRaises(CommandError):
                        call_command('import_stations', str(file), verbosity=0)
                    self.assertEqual(Station.objects.count(), 1)
                    self.assertEqual(Station.objects.get(pk='seed').name, 'Original')
                    self.assertEqual(
                        DatasetState.objects.get(key='stations').digest,
                        'existing-version',
                    )


if __name__ == '__main__':
    import unittest
    unittest.main()
