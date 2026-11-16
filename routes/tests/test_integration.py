from unittest.mock import patch
from django.test import TestCase, SimpleTestCase
from django.core.cache import cache
from rest_framework.test import APIClient
from routes.models import City,Station,DatasetState
from routes.services.routing_client import get_route
from routes.services.station_matching import project

class GeometryTests(SimpleTestCase):
    def test_bent_route(self):
        lateral,mile=project((1.01,.5),{'type':'LineString','coordinates':[[0,0],[1,0],[1,1]]},200)
        self.assertLess(lateral,1)
        self.assertGreater(mile,130)
    @patch('routes.services.routing_client.httpx.post')
    @patch.dict('os.environ',{'ORS_API_KEY':'fake-key'})
    def test_client(self,post):
        post.return_value.status_code=200
        post.return_value.json.return_value={'features':[{'geometry':{'type':'LineString','coordinates':[[-87,41],[-86,41]]},'properties':{'summary':{'distance':160934.4,'duration':3600},'segments':[{'distance':160934.4,'duration':3600}]}}]}
        self.assertEqual(get_route([[-87,41],[-86,41]])['distance_miles'],100)
        self.assertEqual(post.call_args.kwargs['json']['coordinates'][0],[-87,41])

class APITests(TestCase):
    def setUp(self):
        cache.clear();self.client=APIClient()
        City.objects.create(name='A',state='IL',latitude=41,longitude=-90)
        City.objects.create(name='B',state='IL',latitude=41,longitude=-85)
        DatasetState.objects.create(key='stations',digest='test')
        Station.objects.create(opis_id='1',name='Truckstop',address='Exit 1',city='Test',state='IL',rack_id='1',price='3',price_min='3',price_max='3',price_observations=1,price_conflict=False,latitude=41,longitude=-87,location_quality='city_approx')
    def route(self,distance,legs):
        return {'geometry':{'type':'LineString','coordinates':[[-90,41],[-87,41],[-85,41]]},'distance_miles':distance,'duration_minutes':distance,'legs_miles':legs}
    def request(self): return {'start':{'city':'A','state':'IL'},'finish':{'city':'B','state':'IL'}}
    def test_short_and_cache(self):
        with patch('routes.services.route_planner.get_route',return_value=self.route(400,[400])) as provider:
            first=self.client.post('/api/v1/routes/optimize/',self.request(),format='json')
            self.assertEqual(first.status_code,200,first.content)
            self.assertEqual(first.data['meta']['routing_api_calls'],1)
            second=self.client.post('/api/v1/routes/optimize/',self.request(),format='json')
            self.assertTrue(second.data['meta']['cache_hit'])
            self.assertEqual(second.data['meta']['routing_api_calls'],0)
            self.assertEqual(provider.call_count,1)
    def test_long_two_calls(self):
        with patch('routes.services.route_planner.get_route',side_effect=[self.route(700,[700]),self.route(720,[390,330])]) as provider:
            result=self.client.post('/api/v1/routes/optimize/',self.request(),format='json')
            self.assertEqual(result.status_code,200,result.content)
            self.assertEqual(provider.call_count,2)
            self.assertEqual(result.data['fuel']['purchased_en_route_gallons'],'22.0000')
            self.assertEqual(result.data['fuel']['purchased_en_route_usd'],'66.00')
    def test_errors_and_demo(self):
        self.assertEqual(self.client.get('/health/').status_code,200)
        self.assertEqual(self.client.get('/demo/').status_code,200)
        self.assertEqual(self.client.post('/api/v1/routes/optimize/',{'start':{'city':'A','state':'ON'}},format='json').status_code,400)
        with patch('routes.services.route_planner.get_route',return_value=self.route(1100,[1100])):
            self.assertEqual(self.client.post('/api/v1/routes/optimize/',self.request(),format='json').status_code,422)

class ImportTests(TestCase):
    def test_deterministic_observed_median_and_idempotency(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from django.core.management import call_command
        with TemporaryDirectory() as directory:
            path=Path(directory)/'prices.csv'
            head='OPIS Truckstop ID,Truckstop Name,Address,City,State,Rack ID,Retail Price\n'
            rows=['1,Alpha,Exit 1,Test,IL,1,4.00','1,Beta,Exit 1,Test,IL,1,3.00','1,Alpha,Exit 1,Test,IL,1,2.00','1,Beta,Exit 1,Test,IL,1,5.00','2,Canada,Highway,Toronto,ON,2,3.00']
            path.write_text(head+'\n'.join(rows)+'\n')
            call_command('import_stations',str(path),verbosity=0)
            self.assertEqual(Station.objects.count(),1)
            station=Station.objects.get(opis_id='1')
            self.assertEqual(station.price,3)
            self.assertTrue(station.price_conflict)
            self.assertEqual(station.price_observations,4)
            path.write_text(head+'\n'.join(reversed(rows))+'\n')
            call_command('import_stations',str(path),verbosity=0)
            self.assertEqual(Station.objects.count(),1)
            self.assertEqual(Station.objects.get(opis_id='1').price,3)
    def test_atomic_malformed_csv(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from django.core.management import call_command
        from django.core.management.base import CommandError
        with TemporaryDirectory() as directory:
            path=Path(directory)/'bad.csv'
            path.write_text('OPIS Truckstop ID,Truckstop Name,Address,City,State,Rack ID,Retail Price\n1,Name,Address,City,IL,3,abc\n')
            with self.assertRaises(CommandError): call_command('import_stations',str(path),verbosity=0)
            self.assertEqual(Station.objects.count(),0)

class LongTripTests(TestCase):
    def setUp(self):
        cache.clear();self.client=APIClient()
        City.objects.create(name='Start',state='IL',latitude=40,longitude=-100)
        City.objects.create(name='End',state='IL',latitude=40,longitude=-80)
        DatasetState.objects.create(key='stations',digest='long')
        for ident,lon,price in [('10',-94,'4'),('20',-87,'3')]:
            Station.objects.create(opis_id=ident,name='Stop '+ident,address='Exit',city='Test',state='IL',rack_id='1',price=price,price_min=price,price_max=price,price_observations=1,price_conflict=False,latitude=40,longitude=lon,location_quality='city_approx')
    def test_over_thousand_multi_stop(self):
        direct={'geometry':{'type':'LineString','coordinates':[[-100,40],[-94,40],[-87,40],[-80,40]]},'distance_miles':1200,'duration_minutes':1100,'legs_miles':[1200]}
        confirmed={**direct,'distance_miles':1250,'legs_miles':[375,440,435]}
        request={'start':{'city':'Start','state':'IL'},'finish':{'city':'End','state':'IL'}}
        with patch('routes.services.route_planner.get_route',side_effect=[direct,confirmed]) as provider:
            response=self.client.post('/api/v1/routes/optimize/',request,format='json')
            self.assertEqual(response.status_code,200,response.content)
            self.assertEqual(len(response.data['stops']),2)
            self.assertEqual(response.data['meta']['routing_api_calls'],2)
            self.assertEqual(provider.call_count,2)
            self.assertEqual(response.data['fuel']['purchased_en_route_gallons'],'75.0000')
    def test_invalid_json_and_key_absence(self):
        malformed=self.client.generic('POST','/api/v1/routes/optimize/',data='{',content_type='application/json')
        self.assertEqual(malformed.status_code,400)
        self.assertEqual(malformed.data['error']['code'],'invalid_json')
        with patch.dict('os.environ',{'ORS_API_KEY':''}):
            response=self.client.post('/api/v1/routes/optimize/',{'start':{'city':'Start','state':'IL'},'finish':{'city':'End','state':'IL'}},format='json')
            self.assertEqual(response.status_code,503)
            self.assertEqual(response.data['error']['code'],'routing_not_configured')

class ProviderErrors(SimpleTestCase):
    @patch.dict('os.environ',{'ORS_API_KEY':'fake-key'})
    @patch('routes.services.routing_client.httpx.post')
    def test_quota_and_bad_shape(self,post):
        from routes.services.routing_client import RoutingError
        post.return_value.status_code=429
        with self.assertRaises(RoutingError) as issue:
            get_route([[0,0],[1,1]])
        self.assertEqual(issue.exception.status,503)
        post.return_value.status_code=200
        post.return_value.json.return_value={'features':[]}
        with self.assertRaises(RoutingError) as issue:
            get_route([[0,0],[1,1]])
        self.assertEqual(issue.exception.code,'routing_response')

class RerouteRegressionTests(TestCase):
    def setUp(self):
        cache.clear(); self.client=APIClient()
        City.objects.create(name='Origin',state='IL',latitude=40,longitude=-100)
        City.objects.create(name='End',state='IL',latitude=40,longitude=-80)
        DatasetState.objects.create(key='stations',digest='reroute')
        for ident,lon,price in [('first',-94,'3'),('second',-88,'4')]:
            Station.objects.create(opis_id=ident,name=ident,address='Exit',city='Test',state='IL',rack_id='1',price=price,price_min=price,price_max=price,price_observations=1,price_conflict=False,latitude=40,longitude=lon,location_quality='city_approx')
    def test_unused_waypoint_requires_third_route(self):
        from routes.services.fuel_optimizer import Offer,D
        stations=list(Station.objects.order_by('opis_id'))
        offers=[(Offer(D(400),D(3),'first'),next(s for s in stations if s.opis_id=='first'),0),
                (Offer(D(800),D(4),'second'),next(s for s in stations if s.opis_id=='second'),0)]
        geometry={'type':'LineString','coordinates':[[-100,40],[-94,40],[-88,40],[-80,40]]}
        def route(distance,legs):
            return {'geometry':geometry,'distance_miles':distance,'duration_minutes':distance,'legs_miles':legs}
        with patch('routes.services.route_planner.candidates',return_value=offers),patch('routes.services.route_planner.get_route',side_effect=[route(1300,[1300]),route(700,[200,200,300]),route(680,[200,480])]) as provider:
            response=self.client.post('/api/v1/routes/optimize/',{'start':{'city':'Origin','state':'IL'},'finish':{'city':'End','state':'IL'}},format='json')
            self.assertEqual(response.status_code,200,response.content)
            self.assertEqual(response.data['meta']['routing_api_calls'],3)
            self.assertEqual(provider.call_count,3)
            self.assertEqual([s['opis_id'] for s in response.data['stops']],['first'])
            self.assertEqual(response.data['route']['distance_miles'],680)
            self.assertFalse(response.data['stops'][0]['station_access_verified'])
    def test_location_version_invalidates_cache(self):
        request={'start':{'city':'Origin','state':'IL'},'finish':{'city':'End','state':'IL'}}
        route={'geometry':{'type':'LineString','coordinates':[[-100,40],[-80,40]]},'distance_miles':400,'duration_minutes':360,'legs_miles':[400]}
        with patch('routes.services.route_planner.get_route',return_value=route) as provider:
            self.client.post('/api/v1/routes/optimize/',request,format='json')
            DatasetState.objects.update_or_create(key='cities',defaults={'digest':'changed'})
            self.client.post('/api/v1/routes/optimize/',request,format='json')
            self.assertEqual(provider.call_count,2)

class InputAndGeometryRegression(SimpleTestCase):
    def test_indexed_projection_near_cell_boundary(self):
        from routes.services.station_matching import PolylineProjector
        geometry={'type':'LineString','coordinates':[[-100.51,40],[-100.49,40],[-99.8,40]]}
        result=PolylineProjector(geometry,100).project((-100.5,40.01))
        self.assertLess(result[0],1)
        self.assertGreaterEqual(result[1],0)
    @patch.dict('os.environ',{'ORS_API_KEY':'fake-key'})
    @patch('routes.services.routing_client.httpx.post')
    def test_nan_distance_is_rejected(self,post):
        from routes.services.routing_client import RoutingError
        post.return_value.status_code=200
        post.return_value.json.return_value={'features':[{'geometry':{'type':'LineString','coordinates':[[0,0],[1,1]]},'properties':{'summary':{'distance':float('nan'),'duration':100},'segments':[{'distance':float('nan'),'duration':100}]}}]}
        with self.assertRaises(RoutingError) as issue: get_route([[0,0],[1,1]])
        self.assertEqual(issue.exception.code,'routing_response')

class InvalidMediaTypeTests(TestCase):
    def test_json_only(self):
        response=APIClient().post('/api/v1/routes/optimize/',{'start':'a','finish':'b'})
        self.assertEqual(response.status_code,415)
        self.assertEqual(response.data['error']['code'],'unsupported_media_type')
