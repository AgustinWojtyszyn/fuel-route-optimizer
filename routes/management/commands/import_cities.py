"""Import the bundled GeoNames cities snapshot distributed with geonamescache."""
import hashlib
from django.core.management.base import BaseCommand
from django.db import transaction
from geonamescache import GeonamesCache
from routes.models import City, Station, DatasetState
from routes.services.locations import normalize
class Command(BaseCommand):
    help = 'Import GeoNames city centroids from geonamescache (not exact station positions).'
    @transaction.atomic
    def handle(self, *args, **kwargs):
        gc = GeonamesCache(min_city_population=500)
        states = gc.get_us_states()
        selected = {}
        for c in gc.get_cities().values():
            if c['countrycode'] != 'US' or c['admin1code'] not in states: continue
            state = c['admin1code']
            if state in ('AK','HI'): continue
            key = (normalize(c['name']),state)
            if key not in selected or c['population'] > selected[key]['population']:
                selected[key] = c
        City.objects.all().delete()
        City.objects.bulk_create([City(name=c['name'],state=state,latitude=float(c['latitude']),longitude=float(c['longitude']),population=max(0,c['population'])) for (_,state),c in selected.items()],batch_size=1000)
        indexed={(name,state):c for (name,state),c in selected.items()}
        stations=list(Station.objects.all())
        for station in stations:
            location=indexed.get((normalize(station.city),station.state))
            station.latitude=float(location['latitude']) if location else None
            station.longitude=float(location['longitude']) if location else None
            station.location_quality='city_approx' if location else 'unlocated'
        if stations:
            Station.objects.bulk_update(stations,['latitude','longitude','location_quality'],batch_size=1000)
        digest=hashlib.sha256(str(sorted((key,c['latitude'],c['longitude']) for key,c in selected.items())).encode()).hexdigest()
        DatasetState.objects.update_or_create(key='cities',defaults={'digest':digest})
        self.stdout.write(f'Imported {len(selected)} city centroids (GeoNames snapshot).')
