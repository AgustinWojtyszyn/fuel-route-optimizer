"""Run the three assessment routes using a real ORS key; save results privately.

Requires ORS_API_KEY in the process environment. Never prints or stores the key.
"""
import json
import os
import sys
import time
from decimal import Decimal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch

if not os.getenv('ORS_API_KEY'):
    sys.exit('ORS_API_KEY is not set; no external requests were made.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
import httpx
from django.core.cache import cache
from django.test import Client

ROUTES = [('los_angeles_las_vegas','Los Angeles','CA','Las Vegas','NV'),
          ('chicago_denver','Chicago','IL','Denver','CO'),
          ('new_york_miami','New York City','NY','Miami','FL')]
out = Path('live_results')
out.mkdir(exist_ok=True)
client = Client()
original_post = httpx.post
for slug,city,state,destination,destination_state in ROUTES:
    cache.clear()
    count=0
    provider_seconds=0.0
    def counted(*args,**kwargs):
        global count,provider_seconds
        count+=1
        started=time.perf_counter()
        try: return original_post(*args,**kwargs)
        finally: provider_seconds+=time.perf_counter()-started
    payload={'start':{'city':city,'state':state},'finish':{'city':destination,'state':destination_state}}
    started=time.perf_counter()
    with patch('routes.services.routing_client.httpx.post',side_effect=counted):
        response=client.post('/api/v1/routes/optimize/',data=json.dumps(payload),content_type='application/json')
    elapsed=time.perf_counter()-started
    result=response.json()
    verified=False
    if response.status_code==200:
        legs=result['route']['leg_distances_miles']
        stops=result['stops']
        assert len(legs)==len(stops)+1
        fuel=Decimal('50')
        for index,leg in enumerate(legs):
            fuel-=Decimal(str(leg))/Decimal('10')
            assert -Decimal('.00001')<=fuel<=50, (slug,index,fuel)
            if index<len(stops):
                fuel+=Decimal(stops[index]['gallons_to_buy'])
                assert -Decimal('.00001')<=fuel<=50, (slug,index,fuel)
        verified=True
        assert count==result['meta']['routing_api_calls']
    (out/f'{slug}.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'route':slug,'http_status':response.status_code,
                      'distance_miles':result.get('route',{}).get('distance_miles'),
                      'duration_minutes':result.get('route',{}).get('duration_minutes'),
                      'stops':len(result.get('stops',[])),
                      'purchased_gallons':result.get('fuel',{}).get('purchased_en_route_gallons'),
                      'purchased_usd':result.get('fuel',{}).get('purchased_en_route_usd'),
                      'estimated_total_usd':result.get('fuel',{}).get('estimated_total_trip_cost_usd'),
                      'provider_requests':count,'provider_seconds':round(provider_seconds,3),
                      'total_seconds':round(elapsed,3),'fuel_legs_checked':verified,
                      'error_code':result.get('error',{}).get('code')}))
