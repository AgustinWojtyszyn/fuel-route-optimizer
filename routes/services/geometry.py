"""Geographic calculations shared by station matching and routing."""
import math

EARTH_MILES = 3958.7613


def haversine(a, b):
    # GeoJSON LineString coordinates may include an elevation dimension.
    lon1, lat1 = map(math.radians, a[:2])
    lon2, lat2 = map(math.radians, b[:2])
    u = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 2*EARTH_MILES*math.asin(min(1, math.sqrt(u)))
