from rest_framework import serializers
from .models import Trip, Day, Place, RouteSegment


class RouteSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteSegment
        fields = ["id", "from_place", "to_place",
                  "distance_km", "travel_time_min"]


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = [
            "id",
            "name",
            "category",
            "start_time",
            "end_time",
            "address",
            "notes",
            "order",
            "latitude",
            "longitude",
            "image_url",
        ]


class DaySerializer(serializers.ModelSerializer):
    places = PlaceSerializer(many=True, read_only=True)

    class Meta:
        model = Day
        fields = ["id", "date", "order", "places"]


class TripSerializer(serializers.ModelSerializer):
    days = DaySerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = [
            "id",
            "user",
            "name",
            "destination_city",
            "start_date",
            "end_date",
            "created_at",
            "share_uuid",
            "days",
        ]
