import hashlib, json
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from rest_framework.exceptions import UnsupportedMediaType
from rest_framework.parsers import JSONParser
from routes.models import Station, DatasetState
from routes.serializers import RouteSerializer
from routes.services.route_planner import plan, InputError
from routes.services.routing_client import RoutingError

def error(code,message,details=None): return {'error':{'code':code,'message':message,'details':details or {}}}
class OptimizeView(APIView):
    parser_classes=[JSONParser]
    authentication_classes=[]
    permission_classes=[]
    def handle_exception(self, exc):
        if isinstance(exc, ParseError):
            return Response(error('invalid_json','Malformed JSON body.'),status=400)
        if isinstance(exc, UnsupportedMediaType):
            return Response(error('unsupported_media_type','Use application/json.'),status=415)
        return super().handle_exception(exc)
    def post(self,request):
        serializer=RouteSerializer(data=request.data)
        if not serializer.is_valid(): return Response(error('invalid_input','Invalid route request.',serializer.errors),status=400)
        payload=serializer.validated_data
        versions=dict(DatasetState.objects.values_list('key','digest'))
        digest=versions.get('stations','no-data')
        location_digest=versions.get('cities','no-cities')
        key='route-v4:'+hashlib.sha256(json.dumps([payload,digest,location_digest],sort_keys=True).encode()).hexdigest()
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
    count=Station.objects.count()
    return JsonResponse({'status':'ok' if count else 'catalog_missing','stations':count},status=200 if count else 503)

def demo(request): return render(request,'routes/demo.html')
