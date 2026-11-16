"""Independent verification of REAL trip outputs; assertions remain active with python -O."""
from decimal import Decimal, ROUND_HALF_UP

TOLERANCE = Decimal('0')
DISTANCE_DISPLAY_TOLERANCE = Decimal('0.00051')
STOP_POSITION_TOLERANCE = Decimal('0.000001')


def decimal(value):
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError('Non-finite fuel or price field')
    return number


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_plan(result, actual_requests):
    route, vehicle, fuel, stops, meta = (
        result['route'], result['vehicle'], result['fuel'], result['stops'], result['meta']
    )
    require(type(actual_requests) is int and 1 <= actual_requests <= 3,
            'Expected one to three provider requests')
    require(meta['routing_api_calls'] == actual_requests,
            'Provider request count does not match')
    require(meta['cache_hit'] is False,
            'Live verification must use cold, uncached requests')
    legs = [decimal(x) for x in route['leg_distances_miles']]
    require(len(legs) == len(stops) + 1,
            'Route leg count must equal purchased stops plus one')
    require(all(x > 0 for x in legs), 'All route legs must be positive')
    mpg = decimal(vehicle['mpg'])
    capacity = decimal(vehicle['assumed_tank_gallons'])
    tank = decimal(vehicle['initial_fuel_gallons'])
    require(mpg > 0 and capacity > 0 and 0 <= tank <= capacity,
            'Invalid vehicle or initial fuel')
    # Reconciliation alone can validate a different, internally consistent
    # vehicle. Live assessment evidence must retain the stated assumptions.
    require(mpg == 10, 'Assessment vehicle must use 10 MPG')
    require(capacity == 50, 'Assessment tank capacity must be 50 gallons')
    require(tank == 50, 'Assessment trip must start with a full 50-gallon tank')
    if 'max_range_miles' in vehicle:
        require(decimal(vehicle['max_range_miles']) == 500,
                'Assessment vehicle range must be 500 miles')
    initial = tank
    spent = Decimal(0)
    purchased = Decimal(0)
    progress = Decimal(0)
    for index, leg in enumerate(legs):
        progress += leg
        tank -= leg / mpg
        require(tank >= -TOLERANCE, f'Ran out of fuel on leg {index + 1}')
        tank = max(tank, Decimal(0))
        if index < len(stops):
            stop = stops[index]
            require(abs(decimal(stop['route_mile']) - progress) <= STOP_POSITION_TOLERANCE,
                    f'Stop mile does not match leg geometry at stop {index + 1}')
            require(abs(decimal(stop['fuel_before_stop_gallons']) - tank) <= TOLERANCE,
                    f'Incorrect pre-purchase fuel at stop {index + 1}')
            gallons = decimal(stop['gallons_to_buy'])
            require(gallons > 0, 'Every stop must buy positive fuel')
            tank += gallons
            require(tank <= capacity + TOLERANCE,
                    f'Tank overfilled at stop {index + 1}')
            require(abs(decimal(stop['fuel_after_stop_gallons']) - tank) <= TOLERANCE,
                    f'Incorrect post-purchase fuel at stop {index + 1}')
            receipt = (gallons * decimal(stop['price_usd_per_gallon'])).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            require(decimal(stop['stop_cost_usd']) == receipt,
                    f'Incorrect receipt at stop {index + 1}')
            spent += receipt
            purchased += gallons
    # The public distance is rounded to three decimals; the individual legs
    # remain unrounded for independent fuel accounting.
    require(abs(decimal(route['distance_miles']) - progress) <= DISTANCE_DISPLAY_TOLERANCE,
            'Route total does not match leg distances')
    consumed = sum(legs, Decimal(0)) / mpg
    require(abs(decimal(fuel['consumed_gallons']) - consumed) <= TOLERANCE,
            'Fuel consumption differs from route legs')
    require(abs(decimal(fuel['purchased_en_route_gallons']) - purchased) <= TOLERANCE,
            'Purchase volume differs from stops')
    require(decimal(fuel['purchased_en_route_usd']) == spent,
            'Reported spend differs from station receipts')
    require(abs(decimal(fuel['remaining_at_destination_gallons']) - tank) <= TOLERANCE,
            'Final fuel does not balance')
    require(abs(initial + purchased - consumed - tank) <= TOLERANCE,
            'Fuel mass balance is inconsistent')
    reference = decimal(fuel['initial_fuel_reference_price_usd_per_gallon'])
    require(reference > 0, 'Invalid initial fuel reference price')
    initial_cost = (min(consumed, initial) * reference).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    require(decimal(fuel['initial_fuel_estimated_cost_usd']) == initial_cost,
            'Estimated initial-fuel cost is inconsistent with reference price')
    require(decimal(fuel['estimated_total_trip_cost_usd']) ==
            decimal(fuel['initial_fuel_estimated_cost_usd']) + spent,
            'Estimated total cost does not reconcile')
    return True
