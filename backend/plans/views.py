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
from .models import RouteSegment, Trip, Day, Place
from .serializers import DaySerializer, TripSerializer, PlaceSerializer
from . import ai_planner
from .utils.fetch_image import fetch_image_url
from .utils.convert_coordinate import get_coordinate_from_address
from .utils.fetch_route_between_points import fetch_route_between_points

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

        # If place_id is provided -> UPDATE instead of CREATE
        if place_id:
            return self._update_place(request, day_obj, place_id)
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

            # shift later places to make room for the new place
            if insertion_order <= max_order:
                Place.objects.filter(day=day_obj, order__gte=insertion_order).update(
                    order=F('order') + 1)
            assign_order = insertion_order

        # fetch image
        image_url = fetch_image_url(data.get("name", ""))
        data["image_url"] = image_url

        # Convert address to coordinates
        longitude, latitude = get_coordinate_from_address(data.get("address", ""))
        data["longitude"] = longitude
        data["latitude"] = latitude
        
        serializer = PlaceSerializer(data=data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        place = serializer.save(day=day_obj, order=assign_order)

        prev_place = (
            Place.objects.filter(day=day_obj, order=assign_order - 1).first()
        )
        next_place = (
            Place.objects.filter(day=day_obj, order=assign_order + 1).first()
        )

        # if inserting in the middle, remove old route segment between prev and next
        if prev_place and next_place:
            RouteSegment.objects.filter(
                from_place=prev_place,
                to_place=next_place
            ).delete()

        # create new route segments involving the new place
        if prev_place:
            route_data = fetch_route_between_points(
                [prev_place.longitude, prev_place.latitude],
                [place.longitude, place.latitude] # type: ignore
            )
            if route_data:
                RouteSegment.objects.create(
                    route_id=f"route-{prev_place.id}-{place.id}", # type: ignore
                    from_place=prev_place,
                    to_place=place,
                    distance_km=route_data['distance'] / 1000.0,
                    travel_time_min=route_data['duration'] / 60.0,
                    coordinates=route_data['coordinates']
                )

        if next_place:
            route_data = fetch_route_between_points(
                [place.longitude, place.latitude], # type: ignore
                [next_place.longitude, next_place.latitude]
            )
            if route_data:
                RouteSegment.objects.create(
                    route_id=f"route-{place.id}-{next_place.id}", # type: ignore
                    from_place=place,
                    to_place=next_place,
                    distance_km=route_data['distance'] / 1000.0,
                    travel_time_min=route_data['duration'] / 60.0,
                    coordinates=route_data['coordinates']
                )

        return Response(PlaceSerializer(place).data, status=status.HTTP_201_CREATED)
    
    def _update_place(self, request, day_obj, place_id):
        place = get_object_or_404(Place, pk=place_id, day=day_obj)
        data = request.data.copy()

        # Track whether name or image is updated
        name_changed = "name" in data and data["name"] != place.name
        address_changed = "address" in data and data["address"] != place.address
        image_requested = "image_url" in data  # explicitly indicated by frontend
        start_time_changed = (
            "start_time" in data and str(data["start_time"]) != str(place.start_time)
        )

        # if user requested new image or place name changed, fetch new image
        if image_requested or name_changed:
            place.image_url = fetch_image_url(data.get("name", ""))

        # if place name changed, update the coordinates
        if name_changed or address_changed:
            longitude, latitude = get_coordinate_from_address(data.get("address", ""))
            place.longitude = longitude
            place.latitude = latitude

        # update mutable fields
        for field in [
            "name",
            "address",
            "start_time",
            "end_time",
            "notes",
            "category",
        ]:
            if field in data:
                setattr(place, field, data[field])

        place.save()
        
        # If start_time changed, we may need to reorder places
        if start_time_changed:
            self._reorder_places(day_obj, place.id) # type: ignore
            place.refresh_from_db() # refresh to get updated order if changed

        # If name or address changed, we may need to recompute route segments
        if name_changed or address_changed:
            prev_place = (
                Place.objects.filter(day=day_obj, order=place.order - 1).first()
            )
            next_place = (
                Place.objects.filter(day=day_obj, order=place.order + 1).first()
            )

            # update route segment from prev_place to this place
            if prev_place:
                route_data = fetch_route_between_points(
                    [prev_place.longitude, prev_place.latitude],
                    [place.longitude, place.latitude]
                )
                if route_data:
                    RouteSegment.objects.update_or_create(
                        from_place=prev_place,
                        to_place=place,
                        defaults={
                            'route_id': f"route-{prev_place.id}-{place.id}", # type: ignore
                            'distance_km': route_data['distance'] / 1000.0,
                            'travel_time_min': route_data['duration'] / 60.0,
                            'coordinates': route_data['coordinates']
                        }
                    )

            # update route segment from this place to next_place
            if next_place:
                route_data = fetch_route_between_points(
                    [place.longitude, place.latitude],
                    [next_place.longitude, next_place.latitude]
                )
                if route_data:
                    RouteSegment.objects.update_or_create(
                        from_place=place,
                        to_place=next_place,
                        defaults={
                            'route_id': f"route-{place.id}-{next_place.id}", # type: ignore
                            'distance_km': route_data['distance'] / 1000.0,
                            'travel_time_min': route_data['duration'] / 60.0,
                            'coordinates': route_data['coordinates']
                        }
                    )

        serializer = PlaceSerializer(place)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def _reorder_places(self, day_obj, place_id):
        """
        Reorder places by start_time/order, then only update RouteSegments
        for newly changed adjacency pairs (based on place.id).
        """
        # first get the snapshot of current order
        old_places = list(Place.objects.filter(day=day_obj).order_by('order'))
        old_pairs = {
            (old_places[i].id, old_places[i + 1].id) # type: ignore
            for i in range(len(old_places) - 1)
        }

        # then reorder based on start_time/order
        new_places = list(Place.objects.filter(day=day_obj).order_by('start_time', 'order'))
        for index, place in enumerate(new_places, start=1):
            if place.order != index:
                place.order = index
                place.save(update_fields=['order'])

        # compute new adjacency pairs
        new_pairs = {
            (new_places[i].id, new_places[i + 1].id) # type: ignore
            for i in range(len(new_places) - 1)
        }

        # compute differences
        removed_pairs = old_pairs - new_pairs
        added_pairs = new_pairs - old_pairs

        # delete RouteSegments for removed pairs
        for from_id, to_id in removed_pairs:
            RouteSegment.objects.filter(
                from_place_id=from_id,
                to_place_id=to_id
            ).delete()

        # create RouteSegments for added pairs
        for from_id, to_id in added_pairs:
            from_place = Place.objects.get(id=from_id)
            to_place = Place.objects.get(id=to_id)

            if not (from_place and to_place):
                continue

            route_data = fetch_route_between_points(
                [from_place.longitude, from_place.latitude],
                [to_place.longitude, to_place.latitude]
            )
            if route_data:
                RouteSegment.objects.create(
                    route_id=f"route-{from_id}-{to_id}",
                    from_place_id=from_id,
                    to_place_id=to_id,
                    distance_km=route_data['distance'] / 1000.0,
                    travel_time_min=route_data['duration'] / 60.0,
                    coordinates=route_data['coordinates']
                )

        # return true if place_id is involved in any pair in added_pairs,
        # false otherwise
        return any(place_id in pair for pair in added_pairs)


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
