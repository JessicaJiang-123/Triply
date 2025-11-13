import json
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, permissions, status
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.test import APIRequestFactory
from django.db import transaction
from django.db.models import F
from datetime import date, timedelta
from rest_framework.decorators import action
from .models import RouteSegment, Trip, Day, Place
from .serializers import DaySerializer, TripSerializer, PlaceSerializer
from . import ai_planner
from .utils.fetch_image import fetch_image_url
from .utils.convert_coordinate import get_coordinate_from_address
from .utils.fetch_route_between_points import fetch_route_between_points
from .place_ops import create_place_for_day, update_place_for_day

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
        data = getattr(self.request, "data", {})

        destination_city = data.get('destination_city', '').strip()
        main_city_name = destination_city.split(',')[0].strip() if destination_city else ''

        # Fetch image URL based on destination city name
        image_url = fetch_image_url(main_city_name)

        # Fetch coordinates based on destination city
        longitude, latitude = get_coordinate_from_address(destination_city)

        # Save the trip
        trip = serializer.save(
            user=self.request.user,
            image_url=image_url,
            latitude=latitude,
            longitude=longitude
        )
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
        
        return Response({'detail': 'Sharing endpoint not implemented yet.'}, status=status.HTTP_501_NOT_IMPLEMENTED)


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

    @transaction.atomic
    def post(self, request, trip_id, day_id, place_id=None):
        """
        Create a new place for the specified day, or update an existing place
        if place_id is provided.
        """
        trip = get_object_or_404(Trip, pk=trip_id)
        if trip.user != request.user:
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        day_obj = get_object_or_404(Day, pk=day_id, trip=trip)

        # validate request data
        serializer = PlaceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid place data."}, status=status.HTTP_400_BAD_REQUEST)

        # If place_id is provided -> UPDATE instead of CREATE
        if place_id:
            return update_place_for_day(request.data.copy(), day_obj, place_id)
        else:
            return create_place_for_day(request.data.copy(), day_obj)

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

    @transaction.atomic
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

        prev_place = (
            Place.objects.filter(day=day_obj, order=deleted_order - 1).first()
        )
        next_place = (
            Place.objects.filter(day=day_obj, order=deleted_order + 1).first()
        )

        # if deleting from the middle, remove old route segments involving this place
        if prev_place:
            RouteSegment.objects.filter(
                from_place=prev_place,
                to_place=place
            ).delete()

        if next_place:
            RouteSegment.objects.filter(
                from_place=place,
                to_place=next_place
            ).delete()

        # if prev and next exist, create new route segment between them
        if prev_place and next_place:
            route_data = fetch_route_between_points(
                [prev_place.longitude, prev_place.latitude],
                [next_place.longitude, next_place.latitude]
            )
            if route_data:
                RouteSegment.objects.create(
                    route_id=f"route-{prev_place.id}-{next_place.id}", # type: ignore
                    from_place=prev_place,
                    to_place=next_place,
                    distance_km=route_data['distance'] / 1000.0,
                    travel_time_min=route_data['duration'] / 60.0,
                    coordinates=route_data['coordinates']
                )

        place.delete()

        # reorder remaining places
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
    
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    @transaction.atomic
    def post(self, request):
        """
        Receives trip data from AddTripPage, creates Trip/Days,
        calls AI Planner, and creates Places.
        """
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
        
        ## Create Trip and Days using TripViewSet ###

        factory = APIRequestFactory()

        trip_create_request = factory.post(
            "/api/plans/trips/",
            {
                "name": request.data['name'],
                "destination_city": request.data['destination_city'],
                "start_date": request.data["start_date"],
                "end_date": request.data["end_date"],
            },
            format="json"
        )
        trip_create_request.user = request.user
        
        trip_create_view = TripViewSet.as_view({'post': 'create'})
        trip_response = trip_create_view(trip_create_request)

        if trip_response.status_code != status.HTTP_201_CREATED:
            return Response(
                {"detail": "Failed to create trip."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        trip_id = trip_response.data.get('id')

        # load created trip object from DB
        trip = Trip.objects.get(id=trip_id)

        # load created days
        days = list(trip.days.order_by('order')) # type: ignore

        # call AI planner to get place recommendations
        recommendations = ai_planner.generate_trip_recommendations(
            trip_name, destination_city, preferences, num_days
        )

        if recommendations is None:
            # AI planner not available, delete created trip and days
            trip.delete()

            return Response(
                {"detail": "AI planner is busy or not available now, please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        print("AI Recommendations:", json.dumps(recommendations, indent=2))
        
        ### Create Places using PlaceForDayAPIView ###
        place_view = PlaceForDayAPIView.as_view()

        for day_plan in recommendations:
            day_number = day_plan.get('day', None)
            if not day_number:
                continue

            day_index = day_number - 1
            if not (0 <= day_index < len(days)):
                continue

            print(f"Processing day {day_number} with day_id={days[day_index].id}")

            day_obj = days[day_index]

            day_plan_places = day_plan.get('places', [])
            print(f"  Number of places to add: {len(day_plan_places)}")

            for place_info in day_plan_places:
                print(f"    Adding place: {place_info.get('name', 'N/A')}")
                place_request = factory.post(
                    f"/api/plans/trips/{trip_id}/days/{day_obj.id}/places/",
                    place_info,
                    format="json"
                )
                place_request.user = request.user

                place_response = place_view(
                    place_request,
                    trip_id=trip_id,
                    day_id=day_obj.id
                )

                if place_response.status_code not in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
                    print("[Skipped] Warning: Failed to create place via AI planner:", json.dumps(place_info, indent=2))
                    print("  Error response:", place_response.data) # type: ignore
                    continue
                
        serializer = TripSerializer(trip)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
