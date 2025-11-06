from django.db import models
from django.contrib.auth.models import User
import uuid

class Trip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    name = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    share_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    image_url = models.URLField(max_length=1024, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.user})"


class Day(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='days')
    date = models.DateField()
    order = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['trip', 'order'], name='unique_day_order_per_trip')
        ]

    def __str__(self):
        return f"Day {self.order} of {self.trip} - {self.date}"


class Place(models.Model):
    day = models.ForeignKey(Day, on_delete=models.CASCADE, related_name='places')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    notes = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=1024, blank=True)
    address = models.CharField(max_length=512, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['day', 'order'], name='unique_place_order_per_day')
        ]
        ordering = ['order']

    def __str__(self):
        return f"{self.name} (Day {self.day.order} - {self.day.trip.name})"


class RouteSegment(models.Model):
    from_place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='segment_from')
    to_place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='segment_to')
    distance_km = models.FloatField()
    travel_time_min = models.FloatField()
