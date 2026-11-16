from decimal import ROUND_HALF_UP
from statistics import median
from routes.models import Station
from .locations import find_city
from .station_matching import candidates
from .fuel_optimizer import D, Offer, optimize, Infeasible, CAPACITY, MPG
from .routing_client import get_route

class InputError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)

def money(value): return str(D(value).quantize(D('.01'), rounding=ROUND_HALF_UP))
def amount(value): return str(D(value).quantize(D('.0001'), rounding=ROUND_HALF_UP))

def plan(start, finish):
    source=find_city(start['city'],start['state'])
    target=find_city(finish['city'],finish['state'])
    if not source or not target: raise InputError('unknown_city','City and state must match a city in the local US gazetteer.')
    if source.pk==target.pk: raise InputError('same_location','Start and finish must differ.')
    points=[[source.longitude,source.latitude],[target.longitude,target.latitude]]
    direct=get_route(points)
    calls=1
    found=candidates(direct)
    try: preliminary,_=optimize(direct['distance_miles'],[o for o,_,_ in found])
    except Infeasible as exc: raise InputError('no_feasible_fuel_plan',str(exc)) from exc
    station_by_id={s.opis_id:(s,lateral) for _,s,lateral in found}
    chosen=[station_by_id[o.ident][0] for o,_ in preliminary]
    route=direct
    purchases,left=preliminary,D(50)-D(direct['distance_miles'])/MPG if not chosen else D(0)
    if len(chosen)>48: raise InputError('too_many_stops','More than 48 stops would exceed the routing provider limit.')
    for attempt in range(2 if chosen else 0):
        route=get_route([points[0]]+[[s.longitude,s.latitude] for s in chosen]+[points[1]])
        calls+=1
        positions=[]; distance=D(0)
        for station,leg in zip(chosen,route['legs_miles']):
            distance+=D(leg)
            positions.append(Offer(distance,station.price,station.opis_id))
        try: purchases,left=optimize(route['distance_miles'],positions)
        except Infeasible as exc: raise InputError('unverified_fuel_plan','Verified road segments exceed vehicle range.') from exc
        bought_ids={offer.ident for offer,_ in purchases}
        if len(bought_ids)==len(chosen): break
        if attempt == 1:
            raise InputError('unstable_waypoints','The fuel plan changed after the final waypoint route.')
        chosen=[station for station in chosen if station.opis_id in bought_ids]
    else:
        if calls==3 and chosen:
            raise InputError('unstable_waypoints','The final route could not be verified.')
    station_lookup={s.opis_id:s for s in chosen}
    state_prices=list(Station.objects.filter(state=source.state).values_list('price',flat=True))
    if state_prices: reference=D(median(state_prices)); reference_source='state_median'
    else:
        national=list(Station.objects.values_list('price',flat=True))
        if not national: raise InputError('empty_catalog','Import the station CSV before routing.')
        reference=D(median(national)); reference_source='us_median'
    stops=[]; spent=D(0); bought=D(0)
    for offer,gallons in purchases:
        station=station_lookup[offer.ident]
        charge=gallons*station.price;spent+=charge;bought+=gallons
        stops.append({'opis_id':station.opis_id,'name':station.name,'address':station.address,'city':station.city,'state':station.state,'lat':station.latitude,'lon':station.longitude,'location_quality':station.location_quality,'station_access_verified':False,'route_mile':float(offer.mile),'price_usd_per_gallon':str(station.price),'gallons_to_buy':amount(gallons),'stop_cost_usd':money(charge)})
    consumed=D(route['distance_miles'])/MPG
    # The optimizer reaches the finish empty whenever refueling was required.
    if purchases and abs(left) > D('.00001'):
        raise InputError('fuel_accounting','Unexpected fuel balance at destination.')
    estimated=min(consumed,CAPACITY)*reference+spent
    warnings=['Station coordinates are approximate city centers, not verified fuel-pump locations or confirmed station access.', 'Prices are undated observations; USD per gallon is assumed.']
    if chosen: warnings.append('Route visits approximate city waypoints; actual station access remains unverified.')
    return {'route':{'distance_miles':round(route['distance_miles'],3),'duration_minutes':round(route['duration_minutes'],2),'leg_distances_miles':[round(x,6) for x in route['legs_miles']],'geometry':route['geometry'],'provider':'openrouteservice'},'vehicle':{'max_range_miles':500,'mpg':10,'assumed_tank_gallons':50,'initial_fuel_gallons':50},'fuel':{'consumed_gallons':amount(consumed),'purchased_en_route_gallons':amount(bought),'purchased_en_route_usd':money(spent),'estimated_total_trip_cost_usd':money(estimated),'remaining_at_destination_gallons':amount(left),'initial_fuel_reference_price_usd_per_gallon':str(reference),'initial_price_source':reference_source},'stops':stops,'meta':{'routing_api_calls':calls,'station_access_verified':False,'price_policy':'observed_lower_median','warnings':warnings}}
