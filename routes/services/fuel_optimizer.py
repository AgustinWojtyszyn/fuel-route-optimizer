"""Minimum fuel spend along a fixed, ordered route; all quantities are Decimal."""
from dataclasses import dataclass
from decimal import Decimal

D = lambda value: Decimal(str(value))
CAPACITY = D(50)
MPG = D(10)
class Infeasible(ValueError):
    pass

@dataclass(frozen=True)
class Offer:
    mile: Decimal
    price: Decimal
    ident: str

def optimize(distance, offers, initial=CAPACITY):
    distance, fuel = D(distance), D(initial)
    if not distance.is_finite() or not fuel.is_finite() or distance < 0 or not 0 <= fuel <= CAPACITY:
        raise ValueError('Invalid distance or initial fuel')
    stations = sorted((Offer(D(o.mile), D(o.price), o.ident) for o in offers), key=lambda s:(s.mile,s.price,s.ident))
    if any(not s.price.is_finite() or not s.mile.is_finite()
           or s.price <= 0 or not 0 < s.mile < distance for s in stations):
        raise ValueError('Invalid station position or price')
    # Equal-price co-located stations: retain cheapest deterministic identity.
    stations = [s for i,s in enumerate(stations) if i == 0 or s.mile != stations[i-1].mile]
    purchases, position = [], D(0)
    for i, station in enumerate(stations):
        fuel -= (station.mile-position)/MPG
        if fuel < 0: raise Infeasible('No reachable station within remaining range')
        position = station.mile
        cheaper = next((s for s in stations[i+1:] if s.mile-station.mile <= CAPACITY*MPG and s.price < station.price), None)
        target = min(CAPACITY, (cheaper.mile-station.mile)/MPG if cheaper else (distance-station.mile)/MPG)
        buy = max(D(0), target-fuel)
        if buy:
            fuel += buy
            if fuel > CAPACITY: raise AssertionError('Tank overflow')
            purchases.append((station, buy))
    fuel -= (distance-position)/MPG
    if fuel < 0: raise Infeasible('Destination out of range')
    return purchases, fuel
