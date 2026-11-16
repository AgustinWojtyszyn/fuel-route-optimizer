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
