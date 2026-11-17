import os
import math
import logging
import httpx

from .geometry import haversine
URL = 'https://api.heigit.org/openrouteservice/v2/directions/driving-car/geojson'
class RoutingError(Exception):
    def __init__(self, code, message, status=502):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)

def get_route(points):
    key = os.getenv('ORS_API_KEY')
    if not key:
        raise RoutingError('routing_not_configured', 'Set ORS_API_KEY to run live routing.', 503)
    if not 2 <= len(points) <= 50:
        raise RoutingError('too_many_waypoints', 'Route requires 2–50 waypoints.', 422)
    try:
        timeout = float(os.getenv('ORS_TIMEOUT_SECONDS', '20'))
    except ValueError as exc:
        raise RoutingError('routing_configuration','Invalid provider timeout setting.',503) from exc
    if not math.isfinite(timeout) or not 0 < timeout <= 120:
        raise RoutingError('routing_configuration','Provider timeout must be between 0 and 120 seconds.',503)
    try:
        response = httpx.post(URL, headers={'Authorization':key}, json={'coordinates':points, 'instructions':True}, timeout=timeout)
        if response.status_code >= 400:
            logging.getLogger(__name__).warning(
                'HeiGIT routing failed: upstream_http_status=%s waypoints=%s',
                response.status_code, len(points),
            )
        if response.status_code in (401,403,429):
            raise RoutingError('routing_access', 'Routing key or provider quota rejected the request.', 503)
        if response.status_code >= 400:
            raise RoutingError('routing_failed', 'Routing provider could not calculate the route.', 422 if response.status_code in (404, 400) else 502)
        data = response.json()
        feature = data['features'][0]
        geometry, props = feature['geometry'], feature['properties']
        segments = props['segments']
        coords = geometry['coordinates']
        if (geometry['type'] != 'LineString' or not isinstance(coords, list)
                or len(coords) < 2 or not isinstance(segments, list)
                or len(segments) != len(points)-1):
            raise ValueError('Invalid geometry or segment count')
        # GeoJSON positions must contain actual finite JSON numbers. Accepting
        # numeric strings or booleans would let data through this boundary,
        # then crash the map projector with an unhandled TypeError downstream.
        def valid_position(position):
            if not isinstance(position, list) or len(position) not in (2, 3):
                return False
            for value in position:
                if type(value) not in (int, float):
                    return False
                try:
                    if not math.isfinite(value):
                        return False
                except (OverflowError, ValueError):
                    return False
            return -180 <= position[0] <= 180 and -90 <= position[1] <= 90
        if not all(valid_position(position) for position in coords):
            raise ValueError('Invalid geometry coordinates')
        if len(points) > 2:
            waypoint_indexes = props.get('way_points')
            if (
                not isinstance(waypoint_indexes, list)
                or len(waypoint_indexes) != len(points)
                or any(type(index) is not int or not 0 <= index < len(coords) for index in waypoint_indexes)
                or waypoint_indexes != sorted(waypoint_indexes)
            ):
                raise ValueError('Invalid provider waypoint indexes')
            for point, index in zip(points[1:-1], waypoint_indexes[1:-1]):
                if haversine(point, coords[index]) > 0.125:
                    raise RoutingError(
                        'station_route_access', 'The route does not reach a reviewed fuel stop.', 422,
                    )
        # A provider may return a positive summary with collapsed coordinates.
        # Reject it here instead of crashing the station projector with HTTP 500.
        if not any(a[0] != b[0] or a[1] != b[1] for a,b in zip(coords,coords[1:])):
            raise ValueError('Zero-length road geometry')
        measurements = [s['distance'] for s in segments]
        measurements.extend((props['summary']['distance'], props['summary']['duration']))
        # Python converts True to 1.0, but JSON booleans are not provider
        # distance or duration measurements. Reject them at this boundary.
        if any(isinstance(value, bool) for value in measurements):
            raise ValueError('Boolean route measurement')
        distances = [float(s['distance'])/1609.344 for s in segments]
        summary = float(props['summary']['distance'])/1609.344
        duration = float(props['summary']['duration'])/60
        if (not all(math.isfinite(x) and x > 0 for x in distances)
                or not math.isfinite(summary) or summary <= 0
                or not math.isfinite(duration) or duration <= 0
                or abs(sum(distances)-summary) > 0.1):
            raise ValueError('Invalid route distance')
        return {'geometry':geometry,'distance_miles':sum(distances), 'duration_minutes':duration, 'legs_miles':distances}
    except httpx.TimeoutException as exc:
        raise RoutingError('routing_timeout','Routing provider timed out.',504) from exc
    except httpx.RequestError as exc:
        raise RoutingError('routing_network','Routing provider is unavailable.',502) from exc
    except (ValueError, KeyError, IndexError, TypeError, OverflowError) as exc:
        raise RoutingError('routing_response','Routing provider returned an invalid response.',502) from exc
