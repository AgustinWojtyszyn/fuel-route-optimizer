"""Independent checks for route summary and fuel valuation integrity."""
import unittest
from tests.test_core import example_plan
from scripts.verification import verify_plan


class VerificationCompleteness(unittest.TestCase):
    def test_route_mismatch_is_rejected(self):
        value = example_plan()
        value['route']['distance_miles'] = 600
        with self.assertRaisesRegex(ValueError, 'Route total'):
            verify_plan(value, 2)

    def test_stop_mile_mismatch_is_rejected(self):
        value = example_plan()
        value['stops'][0]['route_mile'] = 399
        with self.assertRaisesRegex(ValueError, 'Stop mile'):
            verify_plan(value, 2)

    def test_initial_fuel_cost_cannot_be_detached_from_reference_price(self):
        value = example_plan()
        value['fuel']['initial_fuel_estimated_cost_usd'] = '199.99'
        with self.assertRaisesRegex(ValueError, 'Estimated initial-fuel'):
            verify_plan(value, 2)

    def test_displayed_distance_rounding_tolerance(self):
        value = example_plan()
        value['route']['distance_miles'] = 700.0005
        self.assertTrue(verify_plan(value, 2))

    def test_wrong_initial_price_is_rejected(self):
        value = example_plan()
        value['fuel']['initial_fuel_reference_price_usd_per_gallon'] = '3.00'
        with self.assertRaisesRegex(ValueError, 'Estimated initial-fuel'):
            verify_plan(value, 2)


if __name__ == '__main__':
    unittest.main()
