"""Project approximate station positions onto cumulative road geometry."""
import math
from collections import defaultdict
from routes.models import Station
from .fuel_optimizer import D, Offer
EARTH_MILES = 3958.7613
CELL_DEGREES = 0.5

def haversine(a, b):
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    u = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 2*EARTH_MILES*math.asin(min(1, math.sqrt(u)))

class PolylineProjector:
    """Index geometry once; each point checks only segments in nearby cells."""
    def __init__(self, geometry, distance):
        self.coordinates = geometry['coordinates']
        if len(self.coordinates) < 2: raise ValueError('Route has fewer than two points')
        self.distance = distance
        self.cumulative = [0.0]
        self.cells = defaultdict(set)
        for index, (a,b) in enumerate(zip(self.coordinates,self.coordinates[1:])):
            self.cumulative.append(self.cumulative[-1]+haversine(a,b))
            for x in range(math.floor(min(a[0],b[0])/CELL_DEGREES)-1, math.floor(max(a[0],b[0])/CELL_DEGREES)+2):
                for y in range(math.floor(min(a[1],b[1])/CELL_DEGREES)-1, math.floor(max(a[1],b[1])/CELL_DEGREES)+2):
                    self.cells[(x,y)].add(index)
        if self.cumulative[-1] <= 0: raise ValueError('Zero-length geometry')

    def project(self, point):
        px,py = point
        cell = (math.floor(px/CELL_DEGREES),math.floor(py/CELL_DEGREES))
        best_lateral, best_progress = float('inf'), float('inf')
        for i in sorted(self.cells.get(cell,())):
            a,b = self.coordinates[i:i+2]
            scale = math.cos(math.radians((py+a[1]+b[1])/3))
            ax,ay = a[0]*scale,a[1]
            bx,by = b[0]*scale,b[1]
            x,y = px*scale,py
            dx,dy = bx-ax,by-ay
            t = max(0,min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
            lateral = math.hypot(x-(ax+t*dx),y-(ay+t*dy))*69.05
            progress = self.cumulative[i]+t*(self.cumulative[i+1]-self.cumulative[i])
            # Crossing a loop twice must select the earliest equal-distance pass.
            if (lateral < best_lateral - 1e-9 or
                (abs(lateral-best_lateral) <= 1e-9 and progress < best_progress)):
                best_lateral, best_progress = lateral, progress
        if not math.isfinite(best_lateral):
            return float('inf'), 0.0
        return best_lateral, best_progress/self.cumulative[-1]*self.distance

def project(point, geometry, distance):
    return PolylineProjector(geometry,distance).project(point)

def candidates(route,corridor_miles=12):
    coords = route['geometry']['coordinates']
    minlon,maxlon = min(x[0] for x in coords)-.35,max(x[0] for x in coords)+.35
    minlat,maxlat = min(x[1] for x in coords)-.25,max(x[1] for x in coords)+.25
    qs = Station.objects.filter(longitude__gte=minlon,longitude__lte=maxlon,latitude__gte=minlat,latitude__lte=maxlat)
    projector = PolylineProjector(route['geometry'],route['distance_miles'])
    found = []
    for station in qs.iterator(chunk_size=1000):
        lateral,mile = projector.project((station.longitude,station.latitude))
        if lateral <= corridor_miles and 0 < mile < route['distance_miles']:
            found.append((Offer(D(mile),station.price,station.opis_id),station,lateral))
    return found
