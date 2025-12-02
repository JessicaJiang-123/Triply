from django.db import models
from django.contrib.auth.models import User


class UnsplashImage(models.Model):
    url_hash = models.CharField(max_length=64, unique=True)
    unsplash_url = models.TextField()
    local_image = models.ImageField(upload_to="unsplash/")

    def __str__(self):
        return self.unsplash_url


class Trip(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='trips')
    name = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True) # latitude of destination city
    longitude = models.FloatField(null=True, blank=True) # longitude of destination city
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    image_url = models.TextField(blank=True, null=True)
    unsplash_image = models.ForeignKey(UnsplashImage, on_delete=models.SET_NULL, null=True, blank=True, related_name='trips')
    preferences = models.JSONField(default=list, blank=True) # List of user travel preferences
    shared_users = models.ManyToManyField(User, related_name='shared_trips', blank=True)

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
    """Canonical/shared place feature (Mapbox feature).

    A mapbox_id uniquely identifies a Mapbox feature.
    """
    mapbox_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"SharedPlace {self.name or self.mapbox_id}"


class Place(models.Model):
    day = models.ForeignKey(
        Day, on_delete=models.CASCADE, related_name='places')
    # Mapbox feature identifier
    mapbox_id = models.CharField(max_length=255, blank=True, null=True)
    # Whether this place is fully supported / recognized by Mapbox
    mapbox_supported = models.BooleanField(default=False)
    # Bind to the canonical SharedPlace
    shared_place = models.ForeignKey(
        'SharedPlace', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_places')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, blank=True, null=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    notes = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    description = models.TextField(blank=True)
    image_url = models.TextField(blank=True, null=True)
    unsplash_image = models.ForeignKey(UnsplashImage, on_delete=models.SET_NULL, null=True, blank=True, related_name='places')
    address = models.CharField(max_length=512, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} (Day {self.day.order} - {self.day.trip.name})"


class RouteSegment(models.Model):
    route_id = models.CharField(max_length=100) # e.g., route-<place1_id>-<place2_id>
    from_place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='segment_from')
    to_place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='segment_to')
    distance_km = models.FloatField(null=True, blank=True)
    travel_time_min = models.FloatField(null=True, blank=True)
    coordinates = models.JSONField(null=True, blank=True)  # Store GeoJSON coordinate array
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_place', 'to_place')
        ordering = ['from_place__order']

    def __str__(self):
        return f"{self.from_place.name} -> {self.to_place.name}"


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