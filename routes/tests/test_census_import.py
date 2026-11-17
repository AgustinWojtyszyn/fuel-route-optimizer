"""Regression tests for Census station recovery and safe catalog replacement."""
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from routes.models import City, DatasetState, Station


def make_station(ident, city, *, latitude=None, longitude=None):
    return Station.objects.create(
        opis_id=ident, name=city, address='Route 1', city=city, state='IL',
        rack_id='100', price='3.00', price_min='3.00', price_max='3.00',
        price_observations=1, price_conflict=False,
        latitude=latitude, longitude=longitude,
        location_quality='city_approx' if latitude is not None else 'unlocated',
    )


class CensusStationRecoveryTests(TestCase):
    census = (
        'USPS|NAME|INTPTLAT|INTPTLONG\n'
        'IL|Imaginaryfield city|40.12345|-89.76543\n'
    )

    def setUp(self):
        DatasetState.objects.create(key='cities', digest='original-city-index')
        DatasetState.objects.create(key='stations', digest='original-prices')

    def run_import(self, directory):
        path = Path(directory) / 'census.txt'
        path.write_text(self.census, encoding='utf-8')
        call_command('import_census_places', file=str(path), verbosity=0)

    def test_new_census_place_recovers_unlocated_station_without_replacing_prices(self):
        make_station('1', 'Imaginaryfield')
        make_station('2', 'Imaginaryfield', latitude=41.0, longitude=-88.0)
        with TemporaryDirectory() as directory:
            self.run_import(directory)
            newly_located = Station.objects.get(pk='1')
            self.assertAlmostEqual(newly_located.latitude, 40.12345)
            self.assertAlmostEqual(newly_located.longitude, -89.76543)
            self.assertEqual(newly_located.location_quality, 'city_approx')
            already_located = Station.objects.get(pk='2')
            self.assertEqual((already_located.latitude, already_located.longitude),
                             (41.0, -88.0))
            self.assertEqual(Station.objects.count(), 2)
            self.assertEqual(DatasetState.objects.get(pk='stations').digest,
                             'original-prices')
            self.assertNotEqual(DatasetState.objects.get(pk='cities').digest,
                                'original-city-index')
            self.assertEqual(City.objects.filter(name='Imaginaryfield',
                                                 state='IL').count(), 1)
            version = DatasetState.objects.get(pk='cities').digest
            self.run_import(directory)
            self.assertEqual(DatasetState.objects.get(pk='cities').digest, version)
            self.assertEqual(City.objects.filter(name='Imaginaryfield',
                                                 state='IL').count(), 1)

    def test_existing_census_place_recovers_unlocated_station_on_rerun(self):
        City.objects.create(name='Imaginaryfield', state='IL',
                            latitude=40.12345, longitude=-89.76543)
        make_station('3', 'Imaginaryfield')
        with TemporaryDirectory() as directory:
            self.run_import(directory)
        station = Station.objects.get(pk='3')
        self.assertEqual((station.latitude, station.longitude),
                         (40.12345, -89.76543))
        self.assertNotEqual(DatasetState.objects.get(pk='cities').digest,
                            'original-city-index')


class UsCatalogSafetyTests(TestCase):
    def test_canada_only_file_cannot_erase_existing_us_stations(self):
        make_station('old', 'Chicago')
        DatasetState.objects.create(key='stations', digest='old-data')
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'canada.csv'
            path.write_text(
                'OPIS Truckstop ID,Truckstop Name,Address,City,State,Rack ID,Retail Price\n'
                '123,Truckstop,Exit 1,Toronto,ON,456,3.40\n',
                encoding='utf-8',
            )
            with self.assertRaisesMessage(CommandError, 'No valid US stations'):
                call_command('import_stations', str(path), verbosity=0)
        self.assertEqual(Station.objects.count(), 1)
        self.assertEqual(Station.objects.get(pk='old').name, 'Chicago')
        self.assertEqual(DatasetState.objects.get(pk='stations').digest, 'old-data')
