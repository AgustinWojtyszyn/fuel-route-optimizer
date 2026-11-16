"""Additional assessment checks, using synthetic offers and mocked provider data only."""
from copy import deepcopy
import random
import unittest
from unittest.mock import Mock, patch

from routes.services.fuel_optimizer import CAPACITY, MPG, D, Infeasible, Offer, optimize
from routes.services.routing_client import RoutingError, get_route
from scripts.verification import verify_plan
from test_core import example_plan


def exhaustive_tenth_gallons(distance, stations, initial_miles):
    """DP on all tank levels, in one-mile (0.1-gallon) units; no greedy decisions.

    Prefix minima enumerate all possible arrival levels for every departure
    level, reducing O(capacity²) exhaustive transitions to O(capacity).
    Costs are in one-tenth of one cent, so no rounding enters the comparison.
    """
    costs = {initial_miles: 0}
    position = 0
    for mile, price_cents in stations + [(distance, None)]:
        burn = mile-position
        arriving = {level-burn: cost for level, cost in costs.items() if level >= burn}
        if not arriving:
            return None
        if price_cents is None:
            return min(arriving.values())
        best = None
        costs = {}
        for level in range(501):
            if level in arriving:
                candidate = arriving[level]-level*price_cents
                best = candidate if best is None else min(best, candidate)
            if best is not None:
                costs[level] = best+level*price_cents
        position = mile


class AssessmentOptimizerAudit(unittest.TestCase):
    def test_fractional_purchases_and_partial_initial_tanks_against_dp(self):
        rng = random.Random(20261116)
        for trial in range(750):
            distance = rng.randint(1, 1400)
            positions = sorted(rng.sample(range(1, distance), min(rng.randint(0, 9), distance-1)))
            stations = [(mile, rng.randint(1, 900)) for mile in positions]
            initial_miles = rng.randint(0, 500)
            offers = [Offer(D(mile), D(cents)/100, str(i)) for i, (mile, cents) in enumerate(stations)]
            expected = exhaustive_tenth_gallons(distance, stations, initial_miles)
            if expected is None:
                with self.subTest(trial=trial), self.assertRaises(Infeasible):
                    optimize(distance, offers, initial=D(initial_miles)/10)
                continue
            purchases, remaining = optimize(distance, offers, initial=D(initial_miles)/10)
            actual = sum((offer.price*volume for offer, volume in purchases), D(0))
            self.assertEqual(actual, D(expected)/1000, (trial, stations, initial_miles))
            self.assertGreaterEqual(remaining, 0)
            self.assertLessEqual(remaining, CAPACITY)

    def test_fixed_vehicle_constants_and_unreachable_cheaper_offer(self):
        self.assertEqual((CAPACITY, MPG, CAPACITY*MPG), (D(50), D(10), D(500)))
        # The cheapest station is 501 miles beyond the reachable first station.
        # An algorithm looking only at price must not skip the costly bridge.
        offers = [Offer(D(400), D(5), 'first'), Offer(D(800), D(7), 'bridge'),
                  Offer(D(901), D(1), 'cheap')]
        purchases, remaining = optimize(1100, offers)
        self.assertIn('bridge', [offer.ident for offer, _ in purchases])
        self.assertEqual(sum(volume for _, volume in purchases), D(60))
        self.assertEqual(remaining, 0)

    def test_equal_prices_and_exact_capacity_boundaries(self):
        offers = [Offer(D(500), D('3.25'), 'a'), Offer(D(1000), D('3.25'), 'b')]
        purchases, remaining = optimize(1500, offers)
        self.assertEqual([volume for _, volume in purchases], [D(50), D(50)])
        self.assertEqual(remaining, 0)
        with self.assertRaises(Infeasible):
            optimize(D('1500.0000000001'), offers)


class AssessmentProviderAudit(unittest.TestCase):
    @patch.dict('os.environ', {'ORS_API_KEY': 'synthetic-test-key'})
    @patch('routes.services.routing_client.httpx.post')
    def test_provider_boolean_measurements_are_not_real_numbers(self, post):
        original = {'features': [{'geometry': {'type': 'LineString', 'coordinates': [[-90,40],[-89,40]]},
                    'properties': {'summary': {'distance': 1, 'duration': 60},
                                   'segments': [{'distance': 1}]}}]}
        for field in ('segment', 'summary', 'duration'):
            payload = deepcopy(original)
            props = payload['features'][0]['properties']
            if field == 'segment': props['segments'][0]['distance'] = True
            elif field == 'summary': props['summary']['distance'] = True
            else: props['summary']['duration'] = True
            post.return_value = Mock(status_code=200)
            post.return_value.json.return_value = payload
            with self.subTest(field=field):
                with self.assertRaises(RoutingError) as problem:
                    get_route([[-90,40],[-89,40]])
                self.assertEqual(problem.exception.code, 'routing_response')

    @patch.dict('os.environ', {'ORS_API_KEY': 'synthetic-test-key'})
    @patch('routes.services.routing_client.httpx.post')
    def test_nonpositive_summary_is_rejected_even_within_absolute_tolerance(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {'features': [{'geometry': {'type': 'LineString', 'coordinates': [[-90,40],[-89,40]]}, 'properties': {'summary': {'distance': 0, 'duration': 60}, 'segments': [{'distance': 1}]}}]}
        with self.assertRaises(RoutingError) as problem:
            get_route([[-90,40],[-89,40]])
        self.assertEqual(problem.exception.code, 'routing_response')


class AssessmentVerifierAudit(unittest.TestCase):
    def test_internally_balanced_different_mpg_is_not_the_assessment_vehicle(self):
        result = example_plan()
        result['vehicle']['mpg'] = 20
        result['route']['distance_miles'] = 1400
        result['route']['leg_distances_miles'] = [800, 600]
        result['stops'][0]['route_mile'] = 800
        with self.assertRaisesRegex(ValueError, '10 MPG'):
            verify_plan(result, 2)

    def test_reported_range_cannot_disagree_with_assumptions(self):
        result = example_plan()
        result['vehicle']['max_range_miles'] = 1000
        with self.assertRaisesRegex(ValueError, '500 miles'):
            verify_plan(result, 2)

    def test_larger_tank_is_not_the_assessment_vehicle(self):
        result = example_plan()
        result['vehicle']['assumed_tank_gallons'] = 100
        with self.assertRaisesRegex(ValueError, '50 gallons'):
            verify_plan(result, 2)

    def test_partially_filled_start_is_not_the_api_assumption(self):
        result = example_plan()
        result['vehicle']['initial_fuel_gallons'] = 49
        stop, fuel = result['stops'][0], result['fuel']
        stop.update(gallons_to_buy='21', stop_cost_usd='63.00', fuel_before_stop_gallons='9')
        fuel.update(purchased_en_route_gallons='21', purchased_en_route_usd='63.00',
                    initial_fuel_estimated_cost_usd='196.00', estimated_total_trip_cost_usd='259.00')
        with self.assertRaisesRegex(ValueError, 'full 50-gallon'):
            verify_plan(result, 2)
