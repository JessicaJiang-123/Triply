from django.db import models
from django.contrib.auth.models import User
import uuid


class Trip(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='trips')
    name = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    share_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False)
    image_url = models.URLField(max_length=1024, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.user})"


class Day(models.Model):
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, related_name='days')
    date = models.DateField()
    order = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['trip', 'order'], name='unique_day_order_per_trip')
        ]

    def __str__(self):
        return f"Day {self.order} of {self.trip} - {self.date}"


class SharedPlace(models.Model):
    """Canonical/shared place feature (e.g. Mapbox feature).

    A combination of mapbox_id and worldview uniquely identifies a Mapbox
    feature. Store optional metadata returned from Mapbox in `metadata`.
    """
    # Mapbox feature identifier. We will use mapbox_id as the unique
    # canonical identifier for a shared place.
    mapbox_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"SharedPlace {self.name or self.mapbox_id}"


class Place(models.Model):
    day = models.ForeignKey(
        Day, on_delete=models.CASCADE, related_name='places')
    # Mapbox feature identifier
    mapbox_id = models.CharField(max_length=255, blank=True)
    # Bind to the canonical SharedPlace
    shared_place = models.ForeignKey(
        'SharedPlace', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_places')
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
    from_place = models.ForeignKey(
        Place, on_delete=models.CASCADE, related_name='segment_from')
    to_place = models.ForeignKey(
        Place, on_delete=models.CASCADE, related_name='segment_to')
    distance_km = models.FloatField()
    travel_time_min = models.FloatField()


class PlaceComment(models.Model):
    """User comments bound to a SharedPlace (canonical Mapbox feature).

    Storing comments on the SharedPlace makes them visible across different
    users' `Place` instances that point to the same Mapbox feature.
    """
    shared_place = models.ForeignKey(
        'SharedPlace', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='place_comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user} on {self.shared_place}"


class CommentImage(models.Model):
    """Images attached to a PlaceComment. One comment can have many images."""
    comment = models.ForeignKey(
        'PlaceComment', on_delete=models.CASCADE, related_name='images')
    user = models.ForeignKey(User, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='comment_images')
    image_url = models.URLField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Image for comment {self.comment.id} ({self.image_url})"
