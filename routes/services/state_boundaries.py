"""Point-in-polygon check against the Census 2024 1:5m state boundaries."""
import gzip
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def boundaries():
    path = Path(__file__).resolve().parents[1] / 'geodata' / 'census-2024-states.json.gz'
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        return json.load(stream)


def inside_ring(x, y, ring):
    inside = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:]):
        if (ay > y) != (by > y) and x < ax + (bx - ax) * (y - ay) / (by - ay):
            inside = not inside
    return inside


def point_in_state(latitude, longitude, state):
    return any(
        inside_ring(longitude, latitude, outer)
        and not any(inside_ring(longitude, latitude, hole) for hole in holes)
        for outer, *holes in boundaries().get(state, ())
    )
