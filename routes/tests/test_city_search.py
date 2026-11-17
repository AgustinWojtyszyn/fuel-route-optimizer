"""City lookup and optional U.S. Census catalog import: fully offline tests."""
import os
import tempfile
import zipfile

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from routes.models import City, DatasetState


class CitySearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for name, state, population in [
            ('New York', 'NY', 8000000),
            ('Newark', 'NJ', 300000),
            ('Newark', 'DE', 25000),
            ('New Bern', 'NC', 30000),
            ('Denver', 'CO', 750000),
            ('Chicago', 'IL', 2700000),
        ]:
            City.objects.create(
                name=name, state=state,
                latitude=40.0, longitude=-73.0, population=population,
            )

    def test_prefix_search_returns_only_valid_local_city_pairs(self):
        response = self.client.get('/api/v1/cities/', {'q': 'new'})
        self.assertEqual(response.status_code, 200)
        values = response.json()['results']
        self.assertTrue(values)
        self.assertEqual(values[0], {'name': 'New York', 'state': 'NY'})
        self.assertEqual(
            {(c['name'], c['state']) for c in values},
            {('New York', 'NY'), ('Newark', 'NJ'), ('Newark', 'DE'), ('New Bern', 'NC')},
        )

    def test_state_filter_and_case_insensitivity(self):
        response = self.client.get('/api/v1/cities/', {'q': 'NEW', 'state': 'nJ'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['results'], [{'name': 'Newark', 'state': 'NJ'}]
        )

    def test_empty_short_bad_and_overlong_queries(self):
        for query in ['', 'n']:
            self.assertEqual(
                self.client.get('/api/v1/cities/', {'q': query}).json(),
                {'results': []},
            )
        self.assertEqual(
            self.client.get('/api/v1/cities/', {'q': 'new', 'state': 'xxx'}).status_code,
            400,
        )
        self.assertEqual(
            self.client.get('/api/v1/cities/', {'q': 'X' * 81}).status_code, 400
        )
        self.assertEqual(self.client.post('/api/v1/cities/').status_code, 405)


class CensusImportTests(TestCase):
    def test_offline_zip_import_preserves_existing_city_and_is_idempotent(self):
        City.objects.create(
            name='New York', state='NY',
            latitude=40.7128, longitude=-74.006, population=8000000
        )
        DatasetState.objects.update_or_create(key='cities', defaults={'digest': 'existing'})
        source = (
            'USPS|NAME|INTPTLAT|INTPTLONG\n'
            'NY|New York city|40.7|-74.0\n'
            'IL|Tiny Village village|40.31|-89.43\n'
            'NV|Carson City city|39.16|-119.77\n'
            'ZZ|Unknown city|20.0|-100.0\n'
        ).encode('utf-8')
        with tempfile.TemporaryDirectory() as folder:
            filename = os.path.join(folder, 'census.zip')
            with zipfile.ZipFile(filename, 'w') as archive:
                archive.writestr('2026_Gaz_place_national.txt', source)
            call_command('import_census_places', file=filename, verbosity=0)
            self.assertEqual(City.objects.count(), 3)
            self.assertEqual(City.objects.get(name='New York').latitude, 40.7128)
            self.assertTrue(City.objects.filter(name='Tiny Village', state='IL').exists())
            self.assertTrue(City.objects.filter(name='Carson City', state='NV').exists())
            digest = DatasetState.objects.get(key='cities').digest
            self.assertNotEqual(digest, 'existing')
            call_command('import_census_places', file=filename, verbosity=0)
            self.assertEqual(City.objects.count(), 3)
            self.assertEqual(DatasetState.objects.get(key='cities').digest, digest)

    def test_bad_columns_fail_without_mutating_catalog(self):
        from django.core.management.base import CommandError
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'bad.txt')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('Wrong|Columns\nA|B\n')
            with self.assertRaises(CommandError):
                call_command('import_census_places', file=path, verbosity=0)
            self.assertEqual(City.objects.count(), 0)


class PresentationIntegrationTests(SimpleTestCase):
    def test_landing_explains_product_and_links_to_planner(self):
        page = self.client.get('/')
        self.assertEqual(page.status_code, 200)
        html = page.content.decode('utf-8')
        self.assertIn('href="/demo/"', html)
        self.assertIn('Fuel Route Optimizer', html)
        self.assertIn('Confirm driveway access', html)
        for language in ('en','es','fr','pt'):
            self.assertIn(f'<option value="{language}">', html)

    def test_planner_has_two_accessible_city_combos_and_still_calls_optimizer(self):
        response = self.client.get('/demo/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertEqual(html.count('role="combobox"'), 2)
        self.assertEqual(html.count('role="listbox"'), 2)
        self.assertIn('id="startCityOptions"', html)
        self.assertIn('id="finishCityOptions"', html)
        self.assertIn('/api/v1/cities/?q=', html)
        self.assertIn('/api/v1/routes/optimize/', html)
