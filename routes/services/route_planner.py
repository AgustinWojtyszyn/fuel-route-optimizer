from decimal import ROUND_HALF_UP
from statistics import median
from routes.models import Station, StationLocation
from .locations import find_city
from .station_matching import candidates
from .fuel_optimizer import D, Offer, optimize, Infeasible, CAPACITY, MPG
from .routing_client import RoutingError, get_route

class InputError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)

def cents(value): return D(value).quantize(D('.01'), rounding=ROUND_HALF_UP)
def money(value): return str(cents(value))
def amount(value):
    """Never round away fuel that the itinerary actually needs."""
    number = D(value)
    four_places = number.quantize(D('.0001'))
    return format(four_places, '.4f') if number == four_places else format(number, 'f')

def plan(start, finish):
    source=find_city(start['city'],start['state'])
    target=find_city(finish['city'],finish['state'])
    if not source or not target: raise InputError('unknown_city','City and state must match a city in the local US gazetteer.')
    if source.pk==target.pk: raise InputError('same_location','Start and finish must differ.')
    # Reject incomplete imports before spending a provider request. Without
    # prices the estimated initial-fuel cost cannot be computed; without any
    # located station an itinerary requiring fuel could never be planned.
    if not Station.objects.exists():
        raise InputError('empty_catalog','Import the station CSV before routing.')
    if not StationLocation.objects.filter(
        status=StationLocation.Status.VERIFIED, latitude__isnull=False,
        longitude__isnull=False,
    ).exists():
        raise InputError('station_locations_missing', 'No verified fuel station locations are available.')
    points=[[source.longitude,source.latitude],[target.longitude,target.latitude]]
    direct=get_route(points)
    calls=1
    found = candidates(direct) if D(direct['distance_miles']) > CAPACITY * MPG else []
    try: preliminary,preliminary_left=optimize(direct['distance_miles'],[o for o,_,_ in found])
    except Infeasible as exc: raise InputError('no_feasible_fuel_plan',str(exc)) from exc
    station_by_id={s.opis_id:(s,lateral) for _,s,lateral in found}
    chosen=[station_by_id[o.ident][0] for o,_ in preliminary]
    route=direct
    purchases,left=preliminary,preliminary_left
    if len(chosen)>48: raise InputError('too_many_stops','More than 48 stops would exceed the routing provider limit.')
    for attempt in range(2 if chosen else 0):
        waypoints = [[s.reviewed_location.longitude, s.reviewed_location.latitude] for s in chosen]
        calls += 1
        try:
            route = get_route([points[0], *waypoints, points[1]])
        except RoutingError as exc:
            if attempt or exc.stop_index is None:
                raise
            replacement = alternative_stops(direct['distance_miles'], found, chosen[exc.stop_index].pk)
            if not replacement:
                raise
            chosen = replacement
            continue
        legs = [D(leg) for leg in route['legs_miles']]
        positions = []
        distance = D(0)
        for station, leg in zip(chosen, legs):
            distance += leg
            positions.append(Offer(distance, station.price, station.opis_id))
        try:
            purchases, left = optimize(sum(legs, D(0)), positions)
        except Infeasible as exc:
            if attempt == 0:
                # A projected station can force a longer drive than expected.
                # Exclude the most offset stop bordering an over-range leg.
                adjacent = [
                    station for i, station in enumerate(chosen)
                    if max(legs[i:i + 2]) > CAPACITY * MPG
                ]
                if adjacent:
                    rejected = max(adjacent, key=lambda s: station_by_id[s.opis_id][1])
                    replacement = alternative_stops(direct['distance_miles'], found, rejected.pk)
                    if replacement:
                        chosen = replacement
                        continue
            raise InputError('unverified_fuel_plan', 'Verified road segments exceed vehicle range.') from exc
        bought_ids = {offer.ident for offer, _ in purchases}
        if len(bought_ids) == len(chosen):
            break
        if attempt == 1:
            raise InputError('unstable_waypoints', 'The fuel plan changed after the final waypoint route.')
        chosen = [station for station in chosen if station.opis_id in bought_ids]
    station_lookup={s.opis_id:s for s in chosen}
    state_prices=list(Station.objects.filter(state=source.state).values_list('price',flat=True))
    if state_prices: reference=D(median(state_prices)); reference_source='state_median'
    else:
        national=list(Station.objects.values_list('price',flat=True))
        if not national: raise InputError('empty_catalog','Import the station CSV before routing.')
        reference=D(median(national)); reference_source='us_median'
    stops=[]; spent=D(0); bought=D(0)
    legs=[D(leg) for leg in route['legs_miles']]
    tank=CAPACITY
    for index,(offer,gallons) in enumerate(purchases):
        tank-=legs[index]/MPG
        if tank < 0:
            raise InputError('fuel_accounting','Fuel ran out before a stop.')
        before=max(D(0),tank)
        tank=before+gallons
        if tank > CAPACITY:
            raise InputError('fuel_accounting','Tank was overfilled.')
        station=station_lookup[offer.ident]
        # Each station rounds its own receipt to cents. Sum those receipts,
        # rather than rounding the aggregated unrounded charges.
        charge=cents(gallons*station.price);spent+=charge;bought+=gallons
        location = station.reviewed_location
        stops.append({'opis_id':station.opis_id,'name':station.name,'address':station.address,'city':station.city,'state':station.state,'lat':location.latitude,'lon':location.longitude,'location_quality':location.status,'station_access_verified':location.road_access,'route_mile':float(offer.mile),'price_usd_per_gallon':str(station.price),'gallons_to_buy':amount(gallons),'fuel_before_stop_gallons':amount(before),'fuel_after_stop_gallons':amount(tank),'stop_cost_usd':money(charge)})
    tank-=legs[len(purchases)]/MPG
    if tank < 0 or tank != left:
        raise InputError('fuel_accounting','The route and fuel balances disagree.')
    tank=max(D(0),tank)
    consumed=sum(legs,D(0))/MPG
    initial_cost=cents(min(consumed,CAPACITY)*reference)
    estimated=initial_cost+spent
    warnings=['Prices are undated observations; USD per gallon is assumed.']
    if any(not stop['station_access_verified'] for stop in stops):
        warnings.append('A verified station location does not confirm its driveway access.')
    return {'route':{'distance_miles':round(route['distance_miles'],3),'duration_minutes':round(route['duration_minutes'],2),'leg_distances_miles':list(route['legs_miles']),'geometry':route['geometry'],'provider':'openrouteservice'},'vehicle':{'max_range_miles':500,'mpg':10,'assumed_tank_gallons':50,'initial_fuel_gallons':50},'fuel':{'consumed_gallons':amount(consumed),'purchased_en_route_gallons':amount(bought),'purchased_en_route_usd':money(spent),'initial_fuel_estimated_cost_usd':money(initial_cost),'estimated_total_trip_cost_usd':money(estimated),'remaining_at_destination_gallons':amount(tank),'initial_fuel_reference_price_usd_per_gallon':str(reference),'initial_price_source':reference_source},'stops':stops,'meta':{'routing_api_calls':calls,'station_access_verified':bool(stops) and all(stop['station_access_verified'] for stop in stops),'price_policy':'observed_lower_median','warnings':warnings}}


def alternative_stops(distance, found, excluded_id):
    available = {offer.ident: (offer, station) for offer, station, _ in found
                 if station.pk != excluded_id}
    try:
        purchases, _ = optimize(distance, [offer for offer, _ in available.values()])
    except Infeasible:
        return []
    if len(purchases) > 48:
        return []
    return [available[offer.ident][1] for offer, _ in purchases]
