"""Django integration regression tests for fuel accounting and looped geometry."""
from decimal import Decimal
from unittest.mock import patch
from django.test import SimpleTestCase, TestCase
from routes.models import City, Station
from routes.services.fuel_optimizer import D, Offer
from routes.services.route_planner import amount, plan
from routes.services.station_matching import PolylineProjector


class PrecisionTests(SimpleTestCase):
    def test_gallons_below_four_decimals_are_not_rounded_to_zero(self):
        self.assertEqual(amount(D('0.0000003')), '0.0000003')
        self.assertEqual(amount(D('22')), '22.0000')

    def test_self_crossing_geometry_uses_earliest_pass(self):
        geometry = {'type': 'LineString', 'coordinates': [
            [-100, 40], [-99, 40], [-100, 40], [-99, 40],
        ]}
        lateral, mile = PolylineProjector(geometry, 300).project((-99.5, 40))
        self.assertLess(lateral, 1e-7)
        self.assertAlmostEqual(mile, 50, places=6)


class AccountingTests(TestCase):
    def setUp(self):
        City.objects.create(name='Origin', state='IL', latitude=40, longitude=-100)
        City.objects.create(name='Destination', state='IL', latitude=40, longitude=-90)
        for ident, price in [('one', '0.10'), ('two', '0.01')]:
            Station.objects.create(
                opis_id=ident, name=ident, address='Exit', city='Test',
                state='IL', rack_id='1', price=Decimal(price),
                price_min=Decimal(price), price_max=Decimal(price),
                price_observations=1, price_conflict=False,
                latitude=40, longitude=-95 if ident == 'one' else -92,
                location_quality='city_approx',
            )

    def test_station_receipts_reconcile_to_total(self):
        direct = {
            'geometry': {'type': 'LineString', 'coordinates': [[-100, 40], [-90, 40]]},
            'distance_miles': 505.5, 'duration_minutes': 480,
            'legs_miles': [505.5],
        }
        confirmed = {**direct, 'legs_miles': [498, 2.5, 5]}
        first = Station.objects.get(opis_id='one')
        second = Station.objects.get(opis_id='two')
        found = [
            (Offer(D(498), first.price, first.opis_id), first, 0),
            (Offer(D('500.5'), second.price, second.opis_id), second, 0),
        ]
        with patch('routes.services.route_planner.candidates', return_value=found), patch(
                'routes.services.route_planner.get_route', side_effect=[direct, confirmed]) as provider:
            response = plan({'city': 'Origin', 'state': 'IL'},
                            {'city': 'Destination', 'state': 'IL'})
        self.assertEqual(provider.call_count, 2)
        self.assertEqual([s['gallons_to_buy'] for s in response['stops']], ['0.0500', '0.5000'])
        self.assertEqual([s['stop_cost_usd'] for s in response['stops']], ['0.01', '0.01'])
        self.assertEqual(response['fuel']['purchased_en_route_usd'], '0.02')
        self.assertEqual(response['fuel']['estimated_total_trip_cost_usd'], '2.77')
        self.assertEqual(response['stops'][0]['fuel_before_stop_gallons'], '0.2000')
        self.assertEqual(response['stops'][1]['fuel_after_stop_gallons'], '0.5000')
        self.assertEqual(response['fuel']['remaining_at_destination_gallons'], '0.0000')


class ThrottlingTests(TestCase):
    def test_rate_limit_uses_standard_error_contract(self):
        from django.conf import settings
        from django.core.cache import cache
        from django.test import override_settings
        from rest_framework.test import APIClient
        cache.clear()
        custom = {**settings.REST_FRAMEWORK,
                  'DEFAULT_THROTTLE_RATES': {'fuel_routes': '1/min'}}
        with override_settings(REST_FRAMEWORK=custom):
            client = APIClient()
            first = client.post('/api/v1/routes/optimize/', {}, format='json')
            second = client.post('/api/v1/routes/optimize/', {}, format='json')
            self.assertEqual(first.status_code, 400)
            self.assertEqual(second.status_code, 429)
            self.assertEqual(second.data['error']['code'], 'rate_limited')
        cache.clear()
