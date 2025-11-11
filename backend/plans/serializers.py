from rest_framework import serializers
from .models import Trip, Day, Place, RouteSegment

class RouteSegmentSerializer(serializers.ModelSerializer):
    from_place_name = serializers.CharField(source='from_place.name', read_only=True)
    to_place_name = serializers.CharField(source='to_place.name', read_only=True)

    class Meta:
        model = RouteSegment
        fields = [
            'id',
            'route_id',
            'from_place_name',
            'to_place_name',
            'distance_km',
            'travel_time_min',
            'coordinates',
        ]


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = [
            "id",
            "day",
            "name",
            "category",
            "start_time",
            "end_time",
            "address",
            "notes",
            "order",
            "latitude",
            "longitude",
            "description",
            "image_url",
        ]
        read_only_fields = ['day']

        extra_kwargs = {
            'order': {'required': False}
        }


class DaySerializer(serializers.ModelSerializer):
    places = PlaceSerializer(many=True, read_only=True)
    routes = serializers.SerializerMethodField()

    class Meta:
        model = Day
        fields = ["id", "date", "order", "places", "routes"]

    def get_routes(self, obj):
        route_segments = RouteSegment.objects.filter(
            from_place__day=obj,
            to_place__day=obj
        ).select_related("from_place", "to_place")
        return RouteSegmentSerializer(route_segments, many=True, read_only=True).data


class TripSerializer(serializers.ModelSerializer):
    days = DaySerializer(many=True, read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    firstDayId = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            "id",
            "user",
            "name",
            "destination_city",
            "latitude",
            "longitude",
            "start_date",
            "end_date",
            "created_at",
            "share_uuid",
            "days",
            "image_url",
            "firstDayId",
        ]

    def get_firstDayId(self, obj):
        first_day = obj.days.order_by('order').first()
        return first_day.id if first_day else None
