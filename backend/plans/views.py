from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from .models import Trip
from .serializers import DaySerializer, TripSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Day, Place
from django.db import models as dj_models
from django.db import transaction
from django.db.models import F
from datetime import datetime
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
    permission_classes = [permissions.IsAuthenticated]


class DayForTripAPIView(APIView):
    """
    Retrieve a day for a trip.

    GET: /api/plans/<trip_id>/days/<day_id>/
    """

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get(self, request, trip_id, day_id):
        trip = get_object_or_404(Trip, pk=trip_id)

        # permission check: must be owner
        if trip.user != request.user:
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        day_obj = get_object_or_404(Day, pk=day_id, trip=trip)
        serializer = DaySerializer(day_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PlaceForDayAPIView(APIView):
    """
    Handle retrieving, creating, updating, and deleting places for a day
    while keeping the day's place ordering contiguous.

    POST (create):   /api/plans/<trip_id>/days/<day_id>/places/
    POST (update):   /api/plans/<trip_id>/days/<day_id>/places/<place_id>/
    GET:             /api/plans/<trip_id>/days/<day_id>/places/<place_id>/
    DELETE:          /api/plans/<trip_id>/days/<day_id>/places/<place_id>/
    """

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def post(self, request, trip_id, day_id, place_id=None):
        """
        Create a new place for the specified day, or update an existing place
        if place_id is provided.
        """
        trip = get_object_or_404(Trip, pk=trip_id)
        if trip.user != request.user:
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        day_obj = get_object_or_404(Day, pk=day_id, trip=trip)

        # If place_id is provided -> UPDATE instead of CREATE
        if place_id:
            return self._update_place(request, trip, day_obj, place_id)
        else:
            return self._create_place(request, day_obj)
        
    def _create_place(self, request, day_obj):
        data = request.data.copy()

        start_time_str = data.get('start_time') or None
        new_start = None
        if start_time_str:
            try:
                new_start = datetime.fromisoformat(start_time_str).time()
            except Exception:
                try:
                    new_start = datetime.strptime(start_time_str, '%H:%M').time()
                except Exception:
                    new_start = None

        max_order = (Place.objects.filter(day=day_obj)
                     .aggregate(dj_models.Max('order'))['order__max'] or 0)

        if new_start is None:
            assign_order = max_order + 1
        else:
            # find insertion order
            insertion_order = max_order + 1
            for p in Place.objects.filter(day=day_obj).order_by('order'):
                if p.start_time and new_start and p.start_time > new_start:
                    insertion_order = p.order
                    break

            if insertion_order <= max_order:
                with transaction.atomic():
                    Place.objects.filter(day=day_obj, order__gte=insertion_order).update(
                        order=F('order') + 1)
            assign_order = insertion_order

        place = Place.objects.create(
            day=day_obj,
            name=data.get('name', ''),
            address=data.get('address', ''),
            start_time=data.get('start_time') or None,
            end_time=data.get('end_time') or None,
            notes=data.get('notes', ''),
            order=assign_order,
            image_url=data.get('image_url', ''),
            latitude=data.get('latitude') or 0.0,
            longitude=data.get('longitude') or 0.0,
            category=data.get('category') or '',
        )

        serializer = PlaceSerializer(place)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _update_place(self, request, trip, day_obj, place_id):
        place = get_object_or_404(Place, pk=place_id, day=day_obj)

        data = request.data
        # update mutable fields
        for field in [
            "name",
            "address",
            "start_time",
            "end_time",
            "notes",
            "image_url",
            "latitude",
            "longitude",
            "category",
        ]:
            if field in data:
                setattr(place, field, data[field])

        place.save()
        serializer = PlaceSerializer(place)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def get(self, request, trip_id, day_id, place_id):
        """
        Retrieve a specific place for the specified day
        """
        trip = get_object_or_404(Trip, pk=trip_id)

        # permission check: must be owner
        if trip.user != request.user:
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        day_obj = get_object_or_404(Day, pk=day_id, trip=trip)
        place = get_object_or_404(Place, pk=place_id, day=day_obj)
        serializer = PlaceSerializer(place)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, trip_id, day_id, place_id):
        """
        Delete a specific place for the specified day
        """
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
