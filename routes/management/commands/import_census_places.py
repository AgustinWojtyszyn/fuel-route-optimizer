"""Add official U.S. Census 'Places' centroids to the existing city gazetteer.

This expands selectable incorporated places and census-designated places; it
does not turn approximate positions into verified driving or fuel-pump locations.
2026 Census data: https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html
"""
import csv
import hashlib
import io
import re
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from geonamescache import GeonamesCache

from routes.models import City, DatasetState, Station
from routes.services.locations import normalize


CENSUS_PLACES_URL = (
    'https://www2.census.gov/geo/docs/maps-data/data/gazetteer/'
    '2026_Gazetteer/2026_Gaz_place_national.zip'
)
MAX_ZIP_BYTES = 12 * 1024 * 1024
MAX_TEXT_BYTES = 50 * 1024 * 1024

# The NAME column usually includes the Census geographic type.
PLACE_SUFFIX = re.compile(
    r'\s+(?:city|town|village|borough|CDP|municipality|'
    r'urban county|metro government|metropolitan government|'
    r'consolidated government)(?:\s+\(balance\))?$',
    re.IGNORECASE,
)


def clean_name(value):
    name = (value or '').strip()
    return PLACE_SUFFIX.sub('', name).strip()


def read_archive(data):
    """Read a single Census places table without extracting archive paths."""
    if len(data) > MAX_ZIP_BYTES:
        raise CommandError('Census archive exceeds the allowed size.')
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = [
                item for item in archive.infolist()
                if item.filename.lower().endswith(('.txt', '.tsv'))
                and not item.is_dir()
            ]
            if len(members) != 1:
                raise CommandError('Expected exactly one Census places text file.')
            if members[0].file_size > MAX_TEXT_BYTES:
                raise CommandError('Uncompressed Census table is too large.')
            data = archive.read(members[0])
    if len(data) > MAX_TEXT_BYTES:
        raise CommandError('Census places text is too large.')
    try:
        content = data.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise CommandError('The Census file is not valid UTF-8.') from exc
    reader = csv.DictReader(io.StringIO(content), delimiter='|')
    required = {'USPS', 'NAME', 'INTPTLAT', 'INTPTLONG'}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise CommandError('Incorrect Census Places file (missing required columns).')
    return list(reader)


class Command(BaseCommand):
    help = 'Expand city choices with the official 2026 U.S. Census places gazetteer.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', dest='file', type=str,
            help='Use a previously downloaded Census places .zip or .txt file.',
        )

    def handle(self, *args, **options):
        source = options.get('file')
        if source:
            try:
                data = Path(source).expanduser().read_bytes()
            except OSError as exc:
                raise CommandError(f'Cannot read Census file: {exc}') from exc
        else:
            self.stdout.write('Downloading official 2026 Census Places catalog…')
            try:
                with urllib.request.urlopen(CENSUS_PLACES_URL, timeout=35) as response:
                    data = response.read(MAX_ZIP_BYTES + 1)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                raise CommandError(
                    'Cannot fetch the Census file. Use --file with a local copy.'
                ) from exc

        rows = read_archive(data)
        allowed_states = set(GeonamesCache().get_us_states())
        # The Census includes Puerto Rico, but the routing dataset is US-state
        # oriented; all 50 states and DC are included, including AK and HI.
        allowed_states.discard('PR')
        existing = set(
            (normalize(name), state)
            for name, state in City.objects.values_list('name', 'state')
        )
        to_create = []
        skipped = 0
        for row in rows:
            state = (row.get('USPS') or '').strip().upper()
            name = clean_name(row.get('NAME'))
            if state not in allowed_states or not name or len(name) > 160:
                skipped += 1
                continue
            try:
                lat = float((row.get('INTPTLAT') or '').strip())
                lon = float((row.get('INTPTLONG') or '').strip())
            except ValueError:
                skipped += 1
                continue
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                skipped += 1
                continue
            key = (normalize(name), state)
            if key in existing:
                continue
            existing.add(key)
            to_create.append(City(
                name=name, state=state, latitude=lat, longitude=lon, population=0
            ))

        if not rows:
            raise CommandError('Census places table is empty; no changes made.')
        with transaction.atomic():
            City.objects.bulk_create(to_create, batch_size=1000)

            # Some stations were imported before these places existed. They
            # must be re-matched, including when the Census file is rerun
            # after an older import that left stations unlocated.
            unlocated = Station.objects.filter(
                Q(latitude__isnull=True) | Q(longitude__isnull=True)
            )
            recovered = []
            if unlocated.exists():
                indexed = {
                    (normalize(name), state): (latitude, longitude)
                    for name, state, latitude, longitude in City.objects.values_list(
                        'name', 'state', 'latitude', 'longitude'
                    )
                }
                for station in unlocated.iterator(chunk_size=1000):
                    coords = indexed.get((normalize(station.city), station.state))
                    if coords is None:
                        continue
                    station.latitude, station.longitude = coords
                    station.location_quality = 'city_approx'
                    recovered.append(station)
                if recovered:
                    Station.objects.bulk_update(
                        recovered,
                        ['latitude', 'longitude', 'location_quality'],
                        batch_size=1000,
                    )

            # The route cache includes the cities digest. Recovered station
            # coordinates affect candidate selection even without new places.
            if to_create or recovered:
                previous = DatasetState.objects.filter(key='cities').values_list(
                    'digest', flat=True
                ).first() or ''
                digest = hashlib.sha256(
                    (previous + hashlib.sha256(data).hexdigest()).encode()
                ).hexdigest()
                DatasetState.objects.update_or_create(
                    key='cities', defaults={'digest': digest}
                )
        self.stdout.write(
            self.style.SUCCESS(
                f'Census 2026: added {len(to_create)} places; '
                f'recovered {len(recovered)} approximate station locations; '
                f'skipped {skipped} invalid/out-of-scope rows. '
                'Locations are approximate centroids, not pump addresses.'
            )
        )
