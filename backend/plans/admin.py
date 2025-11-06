from django.contrib import admin
from .models import Trip, Day, Place, RouteSegment

# Register your models here.
@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "destination_city", "user", "start_date", "end_date")
    list_filter = ("destination_city", "user")
    search_fields = ("name", "destination_city", "user__username")

@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ("id", "trip", "date", "order")
    list_filter = ("trip",)

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("id", "day", "name", "start_time", "end_time", "order")
    list_filter = ("day__trip",)

@admin.register(RouteSegment)
class RouteSegmentAdmin(admin.ModelAdmin):
    list_display = ("id", "from_place", "to_place", "distance_km", "travel_time_min")
