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
    image_urls = serializers.ListField(
        child=serializers.URLField(), write_only=True, required=False)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = PlaceComment
        fields = [
            "id",
            "place",
            "user",
            "text",
            "created_at",
            "images",
            "image_urls",
        ]
        read_only_fields = ['place', 'user', 'created_at']

    def create(self, validated_data):
        image_urls = validated_data.pop('image_urls', [])
        if len(image_urls) > 5:
            raise serializers.ValidationError(
                "You can upload a maximum of 5 images per comment.")
        # place and user should be set by view or context
        comment = PlaceComment.objects.create(**validated_data)
        for url in image_urls:
            CommentImage.objects.create(
                comment=comment, image_url=url, user=comment.user)
        return comment
