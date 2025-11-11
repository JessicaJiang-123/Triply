from rest_framework import serializers
from .models import Trip, Day, Place, RouteSegment, PlaceComment, CommentImage


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
            "day",
            "mapbox_id",
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

    class Meta:
        model = Day
        fields = ["id", "date", "order", "places"]


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


class CommentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentImage
        fields = [
            "id",
            "comment",
            "user",
            "image_url",
            "created_at",
        ]
        read_only_fields = ['comment', 'user', 'created_at']


class PlaceCommentSerializer(serializers.ModelSerializer):
    images = CommentImageSerializer(many=True, read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = PlaceComment
        fields = [
            "id",
            "shared_place",
            "user",
            "text",
            "created_at",
            "images",
        ]
        read_only_fields = ['shared_place', 'user', 'created_at']
    
