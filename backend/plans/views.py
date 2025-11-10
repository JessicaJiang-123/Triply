from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, permissions, status
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models as dj_models
from django.db import transaction
from django.db.models import F
from datetime import date, datetime, timedelta
from rest_framework.decorators import action
from .models import Trip, Day, Place
from .serializers import DaySerializer, TripSerializer, PlaceSerializer
from . import ai_planner

# Owner-only retrieve view
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner of the trip.
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'trip'):
            return obj.trip.user == request.user
        if hasattr(obj, 'day'):
            return obj.day.trip.user == request.user
        return False

class TripViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing the user's trips.
    """
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """
        This view should return a list of all the trips
        for the currently authenticated user.
        """
        return Trip.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        trip = serializer.save(user=self.request.user)
        current_date = trip.start_date
        order = 1
        while current_date <= trip.end_date:
            Day.objects.create(
                trip=trip,
                date=current_date,
                order=order
            )
            current_date += timedelta(days=1)
            order += 1

    @action(detail=True, methods=['post'], url_path='share')
    def share_trip(self, request, pk=None):
        trip = self.get_object()
        
        return Response({'message': 'Sharing endpoint not implemented yet.'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class PlanDetailAPIView(generics.RetrieveAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]


class PlanShareAPIView(generics.RetrieveAPIView):
    lookup_field = "share_uuid"
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.AllowAny]


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
        
        serializer = PlaceSerializer(data=data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if assign_order <= max_order:
                Place.objects.filter(day=day_obj, order__gte=assign_order).update(
                    order=F('order') + 1)
            
            place = serializer.save(day=day_obj, order=assign_order)

        return Response(PlaceSerializer(place).data, status=status.HTTP_201_CREATED)
    
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
    

# AI trip planner
class AIGeneratePlanView(APIView):
    """
    Handle generating a new trip plan using the AI Planner.
    POST: /api/plans/generate-ai-plan/
    """
    
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """
        Receives trip data from AddTripPage, creates Trip/Days,
        calls AI Planner, and creates Places.
        """
        
        # get data from frontend (AddTripPage)
        try:
            trip_name = request.data['name']
            destination_city = request.data['destination_city']
            start_date_str = request.data['start_date']
            end_date_str = request.data['end_date']
            preferences = request.data.get('preferences', [])

            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)

            if end_date < start_date:
                return Response(
                    {"detail": "End date cannot be earlier than start date."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            num_days = (end_date - start_date).days + 1

        except (KeyError, ValueError) as e:
            return Response(
                {"detail": f"Invalid or missing data: {e}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # create trip and day objects based on models.py
        try:
            # Trip object (ignore image_url for now)
            new_trip = Trip.objects.create(
                user=request.user,
                name=trip_name,
                destination_city=destination_city,
                start_date=start_date,
                end_date=end_date
            )

            # Day objects
            days_list = []
            current_date = start_date
            for i in range(num_days):
                new_day = Day.objects.create(
                    trip=new_trip,
                    date=current_date,
                    order=i + 1
                )
                days_list.append(new_day)
                current_date += timedelta(days=1)
            
            # call AI planner to get place recommendations
            recommendations = ai_planner.generate_trip_recommendations(
                trip_name, destination_city, preferences, num_days
            )
            
            if recommendations is None:
                raise Exception("AI planner failed to return recommendations.")

            for day_plan in recommendations:
                # (e.g., day_plan = { "day": 1, "places": [...] })
                day_number = day_plan.get('day')
                day_index = day_number - 1
                
                if 0 <= day_index < len(days_list):
                    current_day_object = days_list[day_index]
                    
                    ai_places_list = day_plan.get('places', [])
                    for order_index, place_data in enumerate(ai_places_list):
                        # (e.g., place_data = { "name": "...", "address": "..." })
                        
                        # Place objects (ignore image_url for now)
                        Place.objects.create(
                            day=current_day_object,
                            order=order_index + 1,
                            
                            name=place_data.get('name'),
                            address=place_data.get('address', ''),
                            category=place_data.get('category', ''),
                            start_time=place_data.get('start_time'),
                            end_time=place_data.get('end_time'),
                            notes=place_data.get('notes', '')
                        )


            first_day_id = days_list[0].id if days_list else None
            
            return Response(
                {
                    "trip_id": new_trip.pk,
                    "first_day_id": first_day_id
                },
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            print(f"ERROR: Failed during AI plan creation: {e}")
            return Response(
                {"detail": f"An error occurred while generating the AI plan: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
