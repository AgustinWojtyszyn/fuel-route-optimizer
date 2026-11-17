"""Replay synthetic API outputs through the independent live-evidence verifier.

The provider and station candidates are explicitly mocked. None of these routes,
locations or prices is live provider evidence or evaluation CSV data.
"""
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from .location_fixtures import create_verified_station
from routes.models import City, DatasetState, Station
from routes.services.fuel_optimizer import D, Offer
from scripts.verification import verify_plan


class AssessmentResultContract(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        City.objects.create(name='Synthetic origin', state='IL', latitude=40, longitude=-100)
        City.objects.create(name='Synthetic end', state='IL', latitude=40, longitude=-80)
        DatasetState.objects.create(key='stations', digest='synthetic-assessment-contract')
        self.stations = []
        for ident, longitude, price in [('one', -94, '3'), ('two', -88, '4')]:
            self.stations.append(create_verified_station(
                opis_id=ident, name='Synthetic '+ident, address='Test only', city='Fixture',
                state='IL', rack_id='1', price=D(price), price_min=D(price), price_max=D(price),
                price_observations=1, price_conflict=False, latitude=40, longitude=longitude,
                location_quality='city_approx'))
        self.payload = {'start': {'city': 'Synthetic origin', 'state': 'IL'},
                        'finish': {'city': 'Synthetic end', 'state': 'IL'}}
        self.candidates = [(Offer(D(mile), station.price, station.opis_id), station, 0)
                           for mile, station in zip((400, 800), self.stations)]

    @staticmethod
    def road(distance, legs):
        return {'geometry': {'type': 'LineString', 'coordinates': [[-100,40],[-94,40],[-88,40],[-80,40]]},
                'distance_miles': distance, 'duration_minutes': distance,
                'legs_miles': legs}

    def calculate(self, routes, found=None):
        with patch('routes.services.route_planner.candidates', return_value=self.candidates if found is None else found), \
                patch('routes.services.route_planner.get_route', side_effect=routes) as provider:
            response = self.client.post('/api/v1/routes/optimize/', self.payload, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(verify_plan(response.data, provider.call_count))
        self.assertFalse(response.data['meta']['station_access_verified'])
        for stop in response.data['stops']:
            self.assertFalse(stop['station_access_verified'])
            self.assertEqual(stop['location_quality'], 'verified_exact')
        return response.data, provider.call_count

    def test_short_trip_needs_one_provider_call_and_no_new_fuel(self):
        data, calls = self.calculate([self.road(400, [400])], found=[])
        self.assertEqual(calls, 1)
        self.assertEqual(data['stops'], [])
        self.assertEqual(data['fuel']['purchased_en_route_usd'], '0.00')
        self.assertGreater(D(data['fuel']['initial_fuel_estimated_cost_usd']), 0)

    def test_multiple_purchases_reconcile_after_waypoint_routing(self):
        data, calls = self.calculate([self.road(1200,[1200]), self.road(1250,[375,440,435])])
        self.assertEqual(calls, 2)
        self.assertEqual(len(data['stops']), 2)
        self.assertEqual(data['fuel']['purchased_en_route_gallons'], '75.0000')
        self.assertEqual(sum(D(s['stop_cost_usd']) for s in data['stops']),
                         D(data['fuel']['purchased_en_route_usd']))

    def test_final_waypoint_removal_stays_within_three_calls(self):
        data, calls = self.calculate([self.road(1300,[1300]), self.road(700,[200,200,300]),
                                      self.road(680,[200,480])])
        self.assertEqual(calls, 3)
        self.assertEqual([s['opis_id'] for s in data['stops']], ['one'])

    def test_infeasible_verified_road_leg_is_controlled(self):
        with patch('routes.services.route_planner.candidates', return_value=self.candidates[:1]), \
                patch('routes.services.route_planner.get_route', side_effect=[
                    self.road(800,[800]), self.road(800,[501,299])]) as provider:
            response = self.client.post('/api/v1/routes/optimize/', self.payload, format='json')
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data['error']['code'], 'unverified_fuel_plan')
        self.assertEqual(provider.call_count, 2)

    def test_retries_with_nearer_station_when_detour_breaks_range(self):
        risky, nearby = self.stations
        found = [
            (Offer(D(390), risky.price, risky.opis_id), risky, 8),
            (Offer(D(395), nearby.price, nearby.opis_id), nearby, 1),
        ]
        data, calls = self.calculate([
            self.road(800, [800]),
            self.road(820, [501, 319]),
            self.road(802, [399, 403]),
        ], found=found)
        self.assertEqual(calls, 3)
        self.assertEqual([stop['opis_id'] for stop in data['stops']], [nearby.opis_id])
