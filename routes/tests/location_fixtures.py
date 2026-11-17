from routes.models import Station, StationLocation


def create_verified_station(**fields):
    station = Station.objects.create(**fields)
    StationLocation.objects.create(
        station=station, status=StationLocation.Status.VERIFIED,
        latitude=station.latitude, longitude=station.longitude,
    )
    return station
