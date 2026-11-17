"""Restore the reviewed station locations without modifying the price catalog."""
import base64
import gzip
import hashlib
import io
import json
import math
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from routes.models import City, DatasetState, Station, StationLocation
from routes.services.state_boundaries import point_in_state


def open_manifest(path):
    if path.suffix == '.b64':
        compressed = base64.b64decode(b''.join(path.read_bytes().split()), validate=True)
        return io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(compressed)), encoding='utf-8-sig')
    return path.open(encoding='utf-8-sig')


class Command(BaseCommand):
    help = 'Validate or restore a private JSONL manifest of reviewed station locations.'

    def add_arguments(self, parser):
        parser.add_argument('manifest')
        parser.add_argument('--check', action='store_true')
        parser.add_argument('--min-verified', type=int, default=1)

    @transaction.atomic
    def handle(self, manifest, check, min_verified, **options):
        if min_verified < 1:
            raise CommandError('Minimum verified coverage must be positive.')
        stations = Station.objects.in_bulk()
        allowed = set(StationLocation.Status.values)
        centroids = set(City.objects.values_list('latitude', 'longitude'))
        entries = {}
        coordinates = {}
        verified = 0
        try:
            with open_manifest(Path(manifest)) as stream:
                for line, text in enumerate(stream, 1):
                    row = json.loads(text)
                    ident = row['opis_id']
                    station = stations.get(ident)
                    if station is None or ident in entries:
                        raise ValueError(f'Unknown or duplicate station at line {line}.')
                    state = row['state']
                    status = row['status']
                    if state != station.state or status not in allowed:
                        raise ValueError(f'Invalid state or status at line {line}.')
                    lat, lon = row.get('latitude'), row.get('longitude')
                    if (lat is None) != (lon is None):
                        raise ValueError(f'Incomplete coordinate pair at line {line}.')
                    if lat is not None and (
                        type(lat) not in (int, float) or type(lon) not in (int, float)
                        or not math.isfinite(lat) or not math.isfinite(lon)
                        or not 24 <= lat <= 50 or not -125 <= lon <= -66
                    ):
                        raise ValueError(f'Coordinates outside the contiguous US at line {line}.')
                    evidence = row.get('evidence', [])
                    if not isinstance(evidence, list) or any(
                        not isinstance(item, dict)
                        or not isinstance(item.get('url'), str)
                        or urlsplit(item['url']).scheme != 'https'
                        or not urlsplit(item['url']).hostname
                        or not isinstance(item.get('detail'), str)
                        or not item['detail'].strip()
                        for item in evidence
                    ):
                        raise ValueError(f'Invalid evidence at line {line}.')
                    raw_date = row.get('verified_on')
                    verified_on = date.fromisoformat(raw_date) if raw_date else None
                    source, external_id = row.get('source', ''), row.get('external_id', '')
                    road_access = row.get('road_access_verified', False)
                    if not isinstance(road_access, bool):
                        raise ValueError(f'Invalid road access status at line {line}.')
                    if (
                        not isinstance(source, str) or len(source) > 120
                        or not isinstance(external_id, str) or len(external_id) > 160
                    ):
                        raise ValueError(f'Invalid source identity at line {line}.')
                    if status == StationLocation.Status.VERIFIED:
                        hosts = {urlsplit(item['url']).hostname for item in evidence}
                        if lat is None or (lat, lon) in centroids or len(hosts) < 2 or not (
                            source.strip() and external_id.strip() and verified_on
                        ):
                            raise ValueError(f'Missing independent location evidence at line {line}.')
                        if not point_in_state(lat, lon, state):
                            raise ValueError(f'Coordinates outside the catalog state at line {line}.')
                        rounded = round(lat, 6), round(lon, 6)
                        if rounded in coordinates:
                            raise ValueError(f'Duplicate verified coordinates at line {line}.')
                        coordinates[rounded] = ident
                        verified += 1
                    if road_access and (
                        status != StationLocation.Status.VERIFIED
                        or not any(item.get('kind') == 'road_access' for item in evidence)
                    ):
                        raise ValueError(f'Missing road access evidence at line {line}.')
                    entries[ident] = StationLocation(
                        station_id=ident, status=status, latitude=lat, longitude=lon,
                        source=source, external_id=external_id, verified_on=verified_on,
                        evidence=evidence, road_access_verified=road_access,
                    )
        except (OSError, EOFError, TypeError, ValueError, KeyError, AttributeError) as exc:
            raise CommandError(f'Invalid coordinate manifest: {exc}') from exc
        if verified < min_verified:
            raise CommandError(
                f'Verified locations: {verified}/{len(stations)}. Required: {min_verified}.'
            )
        if not check:
            StationLocation.objects.all().delete()
            StationLocation.objects.bulk_create(entries.values(), batch_size=500)
            digest = hashlib.sha256(
                json.dumps([
                    [key, entry.status, entry.latitude, entry.longitude, entry.source,
                     entry.external_id, str(entry.verified_on), entry.evidence,
                     entry.road_access_verified]
                    for key, entry in sorted(entries.items())
                ], sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()
            DatasetState.objects.update_or_create(
                key='station_locations', defaults={'digest': digest},
            )
        self.stdout.write(f'catalog={len(stations)} reviewed={len(entries)} verified={verified}')
