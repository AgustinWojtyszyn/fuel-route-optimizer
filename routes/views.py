import hashlib, json
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from rest_framework.exceptions import UnsupportedMediaType
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import Throttled
from rest_framework.throttling import ScopedRateThrottle
from routes.models import City, Station, DatasetState, StationLocation
from routes.serializers import RouteSerializer
from routes.services.route_planner import plan, InputError
from routes.services.routing_client import RoutingError

def error(code,message,details=None): return {'error':{'code':code,'message':message,'details':details or {}}}
class OptimizeView(APIView):
    throttle_classes=[ScopedRateThrottle]
    throttle_scope='fuel_routes'
    parser_classes=[JSONParser]
    authentication_classes=[]
    permission_classes=[]
    def handle_exception(self, exc):
        if isinstance(exc, ParseError):
            return Response(error('invalid_json','Malformed JSON body.'),status=400)
        if isinstance(exc, UnsupportedMediaType):
            return Response(error('unsupported_media_type','Use application/json.'),status=415)
        if isinstance(exc, Throttled):
            return Response(error('rate_limited','Too many requests; try again later.'),status=429)
        return super().handle_exception(exc)
    def post(self,request):
        serializer=RouteSerializer(data=request.data)
        if not serializer.is_valid(): return Response(error('invalid_input','Invalid route request.',serializer.errors),status=400)
        payload=serializer.validated_data
        versions=dict(DatasetState.objects.values_list('key','digest'))
        digest=versions.get('stations','no-data')
        location_digest=versions.get('cities','no-cities')
        key='route-v7:'+hashlib.sha256(json.dumps([payload,digest,location_digest,versions.get('station_locations')],sort_keys=True).encode()).hexdigest()
        cached=cache.get(key)
        if cached is not None:
            result=dict(cached);result['meta']={**cached['meta'],'cache_hit':True,'routing_api_calls':0}
            return Response(result)
        try:
            result=plan(**payload)
        except InputError as exc: return Response(error(exc.code,exc.message),status=422)
        except RoutingError as exc: return Response(error(exc.code,exc.message),status=exc.status)
        result['meta']={**result['meta'],'dataset_version':digest,'cache_hit':False}
        cache.set(key,result,86400)
        return Response(result)

def health(request):
    """Local dataset readiness: presence of an API key is NOT provider verification."""
    import os
    station_count = Station.objects.count()
    city_count = City.objects.count()
    located_count = Station.objects.filter(latitude__isnull=False, longitude__isnull=False).count()
    verified_count = StationLocation.objects.filter(
        status=StationLocation.Status.VERIFIED,
        latitude__isnull=False, longitude__isnull=False,
    ).count()
    if not station_count:
        state = 'catalog_missing'
    elif not city_count:
        state = 'gazetteer_missing'
    elif not verified_count:
        state = 'station_locations_missing'
    else:
        state = 'ok'
    return JsonResponse({
        'status': state, 'stations': station_count, 'cities': city_count,
        'located_stations': verified_count,
        'legacy_geocoded_stations': located_count,
        'routing_key_present': bool(os.getenv('ORS_API_KEY')),
        'location_quality': 'verified_establishments' if verified_count else 'city_centroids_only',
        'verified_stations': verified_count,
    }, status=200 if state == 'ok' else 503)

@require_GET
def city_search(request):
    """Autocomplete only against cities the optimizer can resolve locally.

    The API never invents locations or makes per-keystroke routing-provider calls.
    The base GeoNames import is not an exhaustive list of all US settlements.
    """
    query = request.GET.get('q', '').strip()
    state = request.GET.get('state', '').strip().upper()
    if len(query) > 80 or (state and (len(state) != 2 or not state.isascii() or not state.isalpha())):
        return JsonResponse(error('invalid_input', 'Provide a city query up to 80 characters and a two-letter state.'), status=400)
    if len(query) < 2:
        return JsonResponse({'results': []})
    places = City.objects.filter(name__istartswith=query)
    if state:
        places = places.filter(state=state)
    # Only a small page is sent; the browser must not download the entire catalog.
    matches = list(places.order_by('-population', 'name', 'state').values('name', 'state')[:12])
    return JsonResponse({'results': matches})

def landing(request):
    return render(request, 'routes/landing.html')

def demo(request):
    return render(request, 'routes/demo.html')
