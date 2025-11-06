from django.shortcuts import render, get_object_or_404
from rest_framework import generics, permissions
from .models import Trip
from .serializers import TripSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Day, Place
from django.db import models as dj_models
from django.db import transaction
from django.db.models import F
from .serializers import PlaceSerializer


# Owner-only retrieve view
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner of the trip.
        return obj.user == request.user


class PlanDetailAPIView(generics.RetrieveAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]


class PlanShareAPIView(generics.RetrieveAPIView):
    lookup_field = "share_uuid"
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.AllowAny]


class PlaceForDayAPIView(APIView):
    """
    Handle creating a place for a day (POST) and deleting a place (DELETE) while
    keeping the day's place ordering contiguous.

    POST:  /api/plans/<trip_id>/days/<day_id>/places/
    DELETE: /api/plans/<trip_id>/days/<day_id>/places/<place_id>/
    """

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def post(self, request, trip_id, day_id):
        trip = get_object_or_404(Trip, pk=trip_id)

        # permission check: must be owner
        if trip.user != request.user:
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        day_obj = get_object_or_404(Day, pk=day_id, trip=trip)

        data = request.data.copy()

        # compute order for place (append at end)
        next_order = (day_obj.places.aggregate(dj_models.Max('order'))[  # type: ignore
                      'order__max'] or 0) + 1  # type: ignore

        place = Place(
            day=day_obj,
            name=data.get('name', ''),
            address=data.get('address', ''),
            start_time=data.get('start_time') or None,
            end_time=data.get('end_time') or None,
            notes=data.get('notes', ''),
            order=next_order,
            image_url=data.get('image_url', ''),
            latitude=data.get('latitude') or 0.0,
            longitude=data.get('longitude') or 0.0,
            category=data.get('category') or '',
        )

        place.save()

        serializer = PlaceSerializer(place)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, trip_id, day_id, place_id):
        trip = get_object_or_404(Trip, pk=trip_id)

        # permission check: must be owner
        if trip.user != request.user:
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        day_obj = get_object_or_404(Day, pk=day_id, trip=trip)
        place = get_object_or_404(Place, pk=place_id, day=day_obj)

        deleted_order = place.order

        # Perform delete and reorder in a transaction to keep orders contiguous
        with transaction.atomic():
            place.delete()
            # Decrement order for all places in the same day that were after the deleted one
            Place.objects.filter(day=day_obj, order__gt=deleted_order).update(
                order=F('order') - 1)

        # After reordering, return the current list of places for this day so frontend
        # can refresh only the day's content.
        remaining = Place.objects.filter(day=day_obj).order_by('order')
        serializer = PlaceSerializer(remaining, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
