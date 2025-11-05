from django.shortcuts import render, get_object_or_404
from rest_framework import generics, permissions
from .models import Trip
from .serializers import TripSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Day, Place
from django.db import models as dj_models
from .serializers import PlaceSerializer


# Owner-only retrieve view
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS.
        if request.method in permissions.SAFE_METHODS:
            return True
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



class PlaceCreateForDayAPIView(APIView):
    """
    Create a Place under an explicit Day (day_id) belonging to a Trip.
    Endpoint: POST /api/plans/<trip_id>/days/<day_id>/places/
    Body: name, address?, start_time?, end_time?, notes?, image_url?, latitude?, longitude?, category?
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
        next_order = (day_obj.places.aggregate(dj_models.Max('order'))[ # type: ignore
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
