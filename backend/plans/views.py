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

        # Try to parse start_time from input; if invalid or missing, we'll append at end
        start_time_str = data.get('start_time') or None
        new_start = None
        if start_time_str:
            try:
                # accept HH:MM or HH:MM:SS
                new_start = datetime.fromisoformat(start_time_str).time()
            except Exception:
                try:
                    new_start = datetime.strptime(
                        start_time_str, '%H:%M').time()
                except Exception:
                    new_start = None

        # compute max order for the day
        max_order = (Place.objects.filter(day=day_obj).aggregate(
            dj_models.Max('order'))['order__max'] or 0)  # type: ignore

        if new_start is None:
            # append at end
            assign_order = max_order + 1
            place = Place(
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
            place.save()
        else:
            # determine insertion order by comparing to existing places' start_time
            insertion_order = max_order + 1
            for p in Place.objects.filter(day=day_obj).order_by('order'):
                if p.start_time is None:
                    # places without start_time are treated as after timed places
                    continue
                if p.start_time > new_start:
                    insertion_order = p.order
                    break

            with transaction.atomic():
                if insertion_order <= max_order:
                    # shift later places down by +1
                    Place.objects.filter(day=day_obj, order__gte=insertion_order).update(
                        order=F('order') + 1)

                place = Place(
                    day=day_obj,
                    name=data.get('name', ''),
                    address=data.get('address', ''),
                    start_time=data.get('start_time') or None,
                    end_time=data.get('end_time') or None,
                    notes=data.get('notes', ''),
                    order=insertion_order,
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
