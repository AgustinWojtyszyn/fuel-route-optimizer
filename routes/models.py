from django.db import models
class City(models.Model):
    name = models.CharField(max_length=160)
    state = models.CharField(max_length=2)
    latitude = models.FloatField()
    longitude = models.FloatField()
    population = models.PositiveIntegerField(default=0)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['name','state'], name='city_state_unique')]
        indexes = [models.Index(fields=['state','name'])]

class Station(models.Model):
    opis_id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=160)
    state = models.CharField(max_length=2, db_index=True)
    rack_id = models.CharField(max_length=32)
    price = models.DecimalField(max_digits=12, decimal_places=8)
    price_min = models.DecimalField(max_digits=12, decimal_places=8)
    price_max = models.DecimalField(max_digits=12, decimal_places=8)
    price_observations = models.PositiveIntegerField()
    price_conflict = models.BooleanField()
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    location_quality = models.CharField(max_length=32, default='unlocated')
    class Meta:
        indexes = [models.Index(fields=['latitude','longitude'])]

class DatasetState(models.Model):
    key = models.CharField(max_length=32, primary_key=True)
    digest = models.CharField(max_length=64)


class StationLocation(models.Model):
    """Reviewed establishment location, keyed by the original text OPIS ID."""

    class Status(models.TextChoices):
        VERIFIED = 'verified_exact', 'Verified exact'
        HIGH = 'high_confidence', 'High confidence'
        AMBIGUOUS = 'ambiguous', 'Ambiguous'
        UNLOCATED = 'unlocated', 'Unlocated'

    station = models.OneToOneField(Station, primary_key=True, on_delete=models.CASCADE,
                                   related_name='reviewed_location')
    status = models.CharField(max_length=20, choices=Status.choices, db_index=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    source = models.CharField(max_length=120, blank=True)
    external_id = models.CharField(max_length=160, blank=True)
    verified_on = models.DateField(null=True)
    evidence = models.JSONField(default=list)
    road_access_verified = models.BooleanField(default=False)

    @property
    def road_access(self):
        return self.status == self.Status.VERIFIED and self.road_access_verified
