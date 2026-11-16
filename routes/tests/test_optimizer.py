from itertools import product
from django.test import SimpleTestCase
from routes.services.fuel_optimizer import Offer, optimize, Infeasible, D

def exhaustive(distance, stations):
    positions=[0]+[p for p,_ in stations]+[distance]
    states={50:0}
    for i in range(1,len(positions)):
        required=(positions[i]-positions[i-1])//10
        updated={}
        for fuel,cost in states.items():
            remain=fuel-required
            if remain<0: continue
            for buy in (range(51-remain) if i<len(positions)-1 else (0,)):
                new=remain+buy
                amount=cost+buy*stations[i-1][1] if i<len(positions)-1 else cost
                updated[new]=min(updated.get(new,float('inf')),amount)
        states=updated
    return min(states.values()) if states else None

class FuelTests(SimpleTestCase):
    def test_boundaries(self):
        self.assertEqual(optimize(499,[])[0],[])
        self.assertEqual(optimize(500,[])[1],D(0))
        with self.assertRaises(Infeasible): optimize(500.01,[])
        purchases,left=optimize(1200,[Offer(D(400),D(4),'a'),Offer(D(850),D(3),'b')])
        self.assertEqual([s.ident for s,_ in purchases],['a','b'])
        self.assertEqual(left,0)
        self.assertEqual(sum(q for _,q in purchases),D(70))
    def test_exhaustive_price_combinations(self):
        for prices in product((2,3,5),repeat=3):
            stations=list(zip((300,600,900),prices))
            expected=exhaustive(1100,stations)
            purchases,_=optimize(1100,[Offer(D(p),D(v),str(p)) for p,v in stations])
            self.assertEqual(sum(q*s.price for s,q in purchases),D(expected))
    def test_fractional(self):
        purchases,left=optimize(D('500.1'),[Offer(D('499.9'),D('3.1234'),'x')])
        self.assertEqual(purchases[0][1],D('.01'))
        self.assertEqual(left,0)

class LongOptimizerRegressions(SimpleTestCase):
    def test_1600_miles_and_equal_prices(self):
        offers=[Offer(D(mile),D(price),str(mile)) for mile,price in [(400,4),(800,4),(1200,3),(1500,5)]]
        purchases,left=optimize(1600,offers)
        self.assertEqual(left,0)
        self.assertEqual(sum(q for _,q in purchases),D(110))
        self.assertTrue(all(0<q<=50 for _,q in purchases))
        # Simulate every leg independently, including stations without a purchase.
        bought={s.ident:q for s,q in purchases}
        fuel=D(50);position=D(0)
        for stop in offers:
            fuel-=(stop.mile-position)/D(10)
            self.assertGreaterEqual(fuel,0)
            fuel+=bought.get(stop.ident,D(0))
            self.assertLessEqual(fuel,D(50))
            position=stop.mile
        fuel-=(D(1600)-position)/D(10)
        self.assertEqual(fuel,0)
    def test_colocated_and_nonfinite(self):
        purchases,_=optimize(700,[Offer(D(450),D(5),'expensive'),Offer(D(450),D(2),'cheap')])
        self.assertEqual([s.ident for s,_ in purchases],['cheap'])
        with self.assertRaises(ValueError): optimize(D('NaN'),[])
        with self.assertRaises(ValueError): optimize(700,[Offer(D(450),D('Infinity'),'invalid')])
