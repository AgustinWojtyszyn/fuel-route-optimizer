import csv, hashlib
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from routes.models import Station, City, DatasetState
from routes.services.locations import normalize

HEADER = ['OPIS Truckstop ID','Truckstop Name','Address','City','State','Rack ID','Retail Price']
US_STATES = set('AL AZ AR CA CO CT DE FL GA ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())
class Command(BaseCommand):
    help = 'Import supplied CSV (not included in the repository); preserves observed price range.'
    def add_arguments(self, parser): parser.add_argument('csv_path')
    @transaction.atomic
    def handle(self, csv_path, **kwargs):
        path = Path(csv_path)
        if not path.is_file(): raise CommandError('CSV file not found')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        grouped, seen, count, us_count = defaultdict(list),set(),0,0
        try:
            with path.open(newline='',encoding='utf-8-sig') as stream:
                reader = csv.DictReader(stream)
                if reader.fieldnames != HEADER: raise ValueError('CSV headers do not match expected seven columns')
                for line,row in enumerate(reader,2):
                    count += 1
                    if None in row or any(v is None or not v.strip() for v in row.values()): raise ValueError(f'Invalid row {line}')
                    price = Decimal(row['Retail Price'].strip())
                    # DecimalField(max_digits=12, decimal_places=8) must never
                    # silently round an imported price or overflow on write.
                    if (not price.is_finite() or price <= 0 or
                            price > Decimal('9999.99999999') or
                            price != price.quantize(Decimal('0.00000001'))):
                        raise ValueError(f'Invalid or overprecise price at row {line}')
                    ident, rack = row['OPIS Truckstop ID'].strip(), row['Rack ID'].strip()
                    if (not ident.isascii() or not ident.isdecimal() or len(ident) > 32 or
                            not rack.isascii() or not rack.isdecimal() or len(rack) > 32):
                        raise ValueError(f'Invalid ID at row {line}')
                    if (len(row['Truckstop Name'].strip()) > 200 or
                            len(row['Address'].strip()) > 250 or
                            len(row['City'].strip()) > 160 or
                            len(row['State'].strip()) != 2):
                        raise ValueError(f'Invalid text length at row {line}')
                    # Identical source rows do not constitute independent
                    # price observations; counting them skews the lower median.
                    # Normalize padding first to avoid duplicate whitespace.
                    source_row = tuple(row[column].strip() for column in HEADER)
                    duplicate = source_row in seen
                    seen.add(source_row)
                    state = row['State'].strip().upper()
                    if state not in US_STATES: continue
                    us_count += 1
                    if not duplicate:
                        grouped[ident].append((price,row))
        except (OSError, InvalidOperation, ValueError) as exc: raise CommandError(str(exc)) from exc
        cities = {(normalize(c.name),c.state):c for c in City.objects.all()}
        records=[]
        for ident, obs in grouped.items():
            prices=sorted(price for price,_ in obs)
            # Stable canonical metadata, even if input order changes.
            source=min((row for _,row in obs),key=lambda row:tuple(row[k].strip() for k in HEADER))
            city,state=source['City'].strip(),source['State'].strip().upper()
            loc=cities.get((normalize(city),state))
            records.append(Station(opis_id=ident,name=source['Truckstop Name'].strip(),address=source['Address'].strip(),city=city,state=state,rack_id=source['Rack ID'].strip(),price=prices[(len(prices)-1)//2],price_min=prices[0],price_max=prices[-1],price_observations=len(prices),price_conflict=prices[0]!=prices[-1],latitude=loc.latitude if loc else None,longitude=loc.longitude if loc else None,location_quality='city_approx' if loc else 'unlocated'))
        Station.objects.all().delete()
        Station.objects.bulk_create(records,batch_size=1000)
        DatasetState.objects.update_or_create(key='stations', defaults={'digest':digest})
        located=sum(s.latitude is not None for s in records)
        self.stdout.write(f'rows={count} us_rows={us_count} ids={len(records)} exact_duplicates={count-len(seen)} price_conflicts={sum(s.price_conflict for s in records)} located_city_approx={located} unlocated={len(records)-located} sha256={digest}')
