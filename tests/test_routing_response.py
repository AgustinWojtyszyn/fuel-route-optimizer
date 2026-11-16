"""Provider response tests independent of the Django database."""
import unittest
from unittest.mock import patch
from routes.services.routing_client import RoutingError, get_route


def payload(coords):
    return {'features': [{
        'geometry': {'type': 'LineString', 'coordinates': coords},
        'properties': {
            'summary': {'distance': 160934.4, 'duration': 3600},
            'segments': [{'distance': 160934.4, 'duration': 3600}],
        },
    }]}


class RoutingCoordinatesTest(unittest.TestCase):
    def run_route(self, coords):
        with patch.dict('os.environ', {'ORS_API_KEY': 'testing'}), patch(
            'routes.services.routing_client.httpx.post'
        ) as post:
            post.return_value.status_code = 200
            post.return_value.json.return_value = payload(coords)
            return get_route([[-100, 40], [-99, 40]])

    def test_valid_numeric_geojson_2d_and_3d(self):
        self.assertEqual(self.run_route([[-100, 40], [-99, 40]])['distance_miles'], 100)
        self.assertEqual(self.run_route([[-100, 40, 150], [-99, 40, 200]])['distance_miles'], 100)

    def test_malformed_coordinates_fail_as_provider_error(self):
        invalid = [
            [['-100', '40'], ['-99', '40']],
            [[True, 40], [-99, 40]],
            [[-100, 40], [-99, 40, float('nan')]],
            [[], [-99, 40]],
            [[-100, 40], ['-99', 40]],
            [[-100, 40], [-99, 40, 0, 1]],
        ]
        for coords in invalid:
            with self.subTest(coords=coords), self.assertRaises(RoutingError) as raised:
                self.run_route(coords)
            self.assertEqual(raised.exception.code, 'routing_response')
            self.assertEqual(raised.exception.status, 502)


if __name__ == '__main__':
    unittest.main()
