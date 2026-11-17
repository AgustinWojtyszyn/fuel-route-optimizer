"""Run the three assessment routes using a real ORS key; save results privately.

Requires ORS_API_KEY in the process environment. Never prints or stores the key.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.verification import verify_plan
from unittest.mock import patch

ROUTES = [
    ('los_angeles_las_vegas', 'Los Angeles', 'CA', 'Las Vegas', 'NV', 0, 0),
    ('chicago_denver', 'Chicago', 'IL', 'Denver', 'CO', 2, None),
    ('new_york_miami', 'New York City', 'NY', 'Miami', 'FL', 1, None),
]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--case', choices=[route[0] for route in ROUTES],
                    help='Run one cold case to conserve provider quota.')
args = parser.parse_args()
if args.case:
    ROUTES = [route for route in ROUTES if route[0] == args.case]

if not os.getenv('ORS_API_KEY'):
    sys.exit('ORS_API_KEY is not set; no external requests were made.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
import httpx
from django.core.cache import cache
from django.test import Client

out = Path('live_results')
out.mkdir(exist_ok=True)
client = Client()
original_post = httpx.post
failures = 0
for slug, city, state, destination, destination_state, minimum, maximum in ROUTES:
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
    status=None
    result={}
    error_code=None
    verified=False
    try:
        with patch('routes.services.routing_client.httpx.post',side_effect=counted):
            response=client.post('/api/v1/routes/optimize/',data=json.dumps(payload),content_type='application/json')
        status=response.status_code
        result=response.json()
        if status == 200:
            verify_plan(result, count)
            stop_count = len(result['stops'])
            if stop_count < minimum or (maximum is not None and stop_count > maximum):
                error_code = 'unexpected_stop_count'
            else:
                verified = True
        else:
            error_code=result.get('error',{}).get('code','http_error')
    except (ValueError, KeyError, TypeError, ArithmeticError):
        error_code='verification_failed'
    except Exception:
        # Never print upstream exception bodies: provider credentials may be sensitive.
        error_code='request_exception'
    if not verified:
        failures+=1
    elapsed=time.perf_counter()-started
    if result:
        (out/f'{slug}.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'route':slug,'passed':verified,'http_status':status,
                      'distance_miles':result.get('route',{}).get('distance_miles'),
                      'duration_minutes':result.get('route',{}).get('duration_minutes'),
                      'stops':len(result.get('stops',[])),
                      'purchased_gallons':result.get('fuel',{}).get('purchased_en_route_gallons'),
                      'purchased_usd':result.get('fuel',{}).get('purchased_en_route_usd'),
                      'estimated_total_usd':result.get('fuel',{}).get('estimated_total_trip_cost_usd'),
                      'provider_requests':count,'provider_seconds':round(provider_seconds,3),
                      'total_seconds':round(elapsed,3),'fuel_legs_checked':verified,
                      'error_code':error_code}))

print(json.dumps({'cases':len(ROUTES),'passed':len(ROUTES)-failures,'failed':failures,'all_passed':failures==0}))
sys.exit(1 if failures else 0)
