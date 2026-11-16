"""No-Django unit tests: exact optimizer vs independent dynamic programming."""
import random
import unittest

from routes.services.fuel_optimizer import D, Infeasible, Offer, optimize
from scripts.verification import verify_plan


def exhaustive(distance, stations):
    last, costs = 0, {50: 0}
    for i, (mile, price) in enumerate(stations + [(distance, 0)]):
        next_costs = {}
        burn = (mile - last) // 10
        for tank, spent in costs.items():
            after = tank - burn
            if after < 0:
                continue
            for buy in (range(51 - after) if i < len(stations) else (0,)):
                new = after + buy
                cost = spent + buy * price
                next_costs[new] = min(cost, next_costs.get(new, float('inf')))
        costs, last = next_costs, mile
    return min(costs.values()) if costs else None


def example_plan():
    return {
        'route': {'leg_distances_miles': [400, 300]},
        'vehicle': {'mpg': 10, 'assumed_tank_gallons': 50, 'initial_fuel_gallons': 50},
        'stops': [{
            'gallons_to_buy': '20.0000', 'price_usd_per_gallon': '3.00000000',
            'stop_cost_usd': '60.00', 'fuel_before_stop_gallons': '10.0000',
            'fuel_after_stop_gallons': '30.0000',
        }],
        'fuel': {
            'consumed_gallons': '70.0000', 'purchased_en_route_gallons': '20.0000',
            'purchased_en_route_usd': '60.00', 'initial_fuel_estimated_cost_usd': '200.00',
            'estimated_total_trip_cost_usd': '260.00',
            'remaining_at_destination_gallons': '0.0000',
        },
        'meta': {'routing_api_calls': 2, 'cache_hit': False},
    }


class FuelOptimizationTests(unittest.TestCase):
    def test_boundary_and_fractional_gallons_not_rounded(self):
        self.assertEqual(optimize(D('500'), [])[1], D(0))
        with self.assertRaises(Infeasible):
            optimize(D('500.00001'), [])
        offer = Offer(D('499.999999'), D('4.00'), 'station')
        purchases, left = optimize(D('500.000003'), [offer])
        self.assertEqual(purchases, [(offer, D('0.0000003'))])
        self.assertEqual(left, D(0))

    def test_input_validation(self):
        for value in ('NaN', 'Infinity', '-Infinity', '-1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                optimize(D(value), [])
        with self.assertRaises(ValueError):
            optimize(1000, [Offer(D(50), D('NaN'), 'bad')])
        with self.assertRaises(ValueError):
            optimize(1000, [], initial=51)

    def test_randomized_against_independent_exhaustive_search(self):
        rng = random.Random(8246)
        for trial in range(1000):
            n = rng.randint(0, 6)
            prices = [rng.randint(1, 9) for _ in range(n)]
            miles = [x * 10 for x in sorted(rng.sample(range(10, 140), n))]
            destination = rng.randint(miles[-1] // 10 + 1 if miles else 1, 175) * 10
            stations = list(zip(miles, prices))
            offers = [Offer(D(m), D(p), str(i)) for i, (m, p) in enumerate(stations)]
            try:
                purchases, _ = optimize(destination, offers)
                actual = sum((g * s.price for s, g in purchases), D(0))
            except Infeasible:
                actual = None
            self.assertEqual(actual, exhaustive(destination, stations),
                             (trial, destination, stations))

    def test_colocated_equal_price_determinism(self):
        offers = [Offer(D(400), D(5), 'z'), Offer(D(400), D(3), 'b'),
                  Offer(D(400), D(3), 'a')]
        purchases, _ = optimize(D(650), offers)
        self.assertEqual([station.ident for station, _ in purchases], ['a'])

    def test_thousands_of_stations(self):
        offers = [Offer(D(i), D('1.0') + D(i) / 100000, str(i))
                  for i in range(1, 7001)]
        purchases, left = optimize(D(7100), offers)
        self.assertGreater(len(purchases), 0)
        self.assertEqual(left, D(0))


class LiveVerificationTests(unittest.TestCase):
    def test_valid_plan(self):
        self.assertTrue(verify_plan(example_plan(), 2))

    def test_wrong_request_count(self):
        with self.assertRaisesRegex(ValueError, 'Provider request count'):
            verify_plan(example_plan(), 3)

    def test_short_fuel_purchase(self):
        plan = example_plan()
        plan['stops'][0]['gallons_to_buy'] = '19.9999'
        with self.assertRaises(ValueError):
            verify_plan(plan, 2)

    def test_legs_longer_than_capacity(self):
        plan = example_plan()
        plan['route']['leg_distances_miles'] = [501, 199]
        with self.assertRaisesRegex(ValueError, 'Ran out of fuel'):
            verify_plan(plan, 2)

    def test_negative_or_nonfinite_fuel_rejected(self):
        for value in ('NaN', 'Infinity', '-1'):
            plan = example_plan()
            plan['stops'][0]['gallons_to_buy'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                verify_plan(plan, 2)

    def test_understated_receipt_rejected(self):
        plan = example_plan()
        plan['stops'][0]['stop_cost_usd'] = '59.99'
        with self.assertRaisesRegex(ValueError, 'receipt'):
            verify_plan(plan, 2)

    def test_inaccurate_total_rejected(self):
        plan = example_plan()
        plan['fuel']['estimated_total_trip_cost_usd'] = '259.99'
        with self.assertRaisesRegex(ValueError, 'cost does not reconcile'):
            verify_plan(plan, 2)

    def test_cache_hit_is_not_live_evidence(self):
        plan = example_plan()
        plan['meta']['cache_hit'] = True
        with self.assertRaisesRegex(ValueError, 'uncached'):
            verify_plan(plan, 2)


if __name__ == '__main__':
    unittest.main()
