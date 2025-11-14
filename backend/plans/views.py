import json
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, permissions, status
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from django.db import transaction
from datetime import date
from rest_framework.decorators import action

from .services import ai_planner_service, place_service, trip_service
from .models import Trip, Day, Place, PlaceComment, CommentImage, SharedPlace
from .serializers import DaySerializer, TripSerializer, PlaceSerializer, PlaceCommentSerializer, CommentImageSerializer

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from urllib.parse import urljoin, urlparse, unquote
import os
import uuid

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

    @transaction.atomic
    def perform_create(self, serializer):
        validated_data = serializer.validated_data.copy()
        trip = trip_service.create_trip_with_days(user=self.request.user, validated_data=validated_data)
        serializer.instance = trip

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
        # validate request data
        serializer = PlaceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid place data."}, status=status.HTTP_400_BAD_REQUEST)
        
        _, day_obj = place_service.get_trip_and_day_for_user(trip_id, day_id, request.user)

        try:
            # If place_id is provided -> UPDATE instead of CREATE
            if place_id:
                place = place_service.update_place_for_day(request.data.copy(), day_obj, place_id)
                status_code = status.HTTP_200_OK
            else:
                place = place_service.create_place_for_day(request.data.copy(), day_obj)
                status_code = status.HTTP_201_CREATED
        except (ValueError, ValidationError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(PlaceSerializer(place).data, status=status_code)

    def get(self, request, trip_id, day_id, place_id):
        """
        Retrieve a specific place for the specified day
        """
        _, day_obj = place_service.get_trip_and_day_for_user(trip_id, day_id, request.user)
        place = get_object_or_404(Place, pk=place_id, day=day_obj)
        serializer = PlaceSerializer(place)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, trip_id, day_id, place_id):
        """
        Delete a specific place for the specified day
        """
        _, day_obj = place_service.get_trip_and_day_for_user(trip_id, day_id, request.user)
        remaining_places = place_service.delete_place_for_day(day_obj, place_id)
        serializer = PlaceSerializer(remaining_places, many=True)
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
        recommendations = ai_planner_service.generate_trip_recommendations(
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


class PlaceCommentImagesAPIView(APIView):
    """Return a small set of comment images for a place (for a right-top preview)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, mapbox_id):
        # Directly resolve the SharedPlace from provided mapbox_id
        shared_place = get_object_or_404(SharedPlace, mapbox_id=mapbox_id)
        limit = 5 # show up to 5 images
        
        # Return the most recent comment images for the place (global recent)
        images = list(CommentImage.objects.filter(comment__shared_place=shared_place).order_by('-created_at')[:limit])

        return Response(CommentImageSerializer(images, many=True).data, status=status.HTTP_200_OK)


class PlaceCommentAPIView(APIView):
    
    # default for non-GET requests
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        # Allow anonymous GET (listing comments) but require auth for POST
        if getattr(self, 'request', None) and self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def post(self, request, mapbox_id):
        """Create a comment for a SharedPlace identified by mapbox_id in the URL.

        Endpoint: POST /api/plans/places/by-mapbox/<mapbox_id>/comments/
        Payload: { "text": "...", "image_urls": [...], optional other fields }
        """
        shared_place = get_object_or_404(SharedPlace, mapbox_id=mapbox_id)

        text = request.data.get('text', '')
        raw_image_urls = request.data.get('image_urls', [])

        # Normalize incoming image_urls which may be strings or objects like {image_url: "..."}
        if not isinstance(raw_image_urls, list):
            return Response({"image_urls": "must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        image_urls: list[str] = []
        for it in raw_image_urls:
            if isinstance(it, str):
                image_urls.append(it)
            elif isinstance(it, dict) and 'image_url' in it:
                val = it.get('image_url')
                if isinstance(val, str):
                    image_urls.append(val)
        # enforce max images
        if len(image_urls) > 3:
            return Response({"image_urls": "You can upload a maximum of 3 images per comment."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate each URL comes from our MEDIA_URL and that the file exists in storage
        def _storage_path_from_url(u: str) -> str | None:
            try:
                parsed = urlparse(u)
            except Exception:
                return None
            # Prefer parsed.path check (handles absolute and relative URLs)
            path = parsed.path or u
            # URL-decode the path to match storage keys (handles %20 etc.)
            path_unquoted = unquote(path)
            if path_unquoted.startswith(settings.MEDIA_URL):
                # strip leading MEDIA_URL
                storage_path = path_unquoted[len(settings.MEDIA_URL):].lstrip('/')
                return storage_path
            # also allow bare relative urls starting with MEDIA_URL
            if u.startswith(settings.MEDIA_URL):
                return unquote(u[len(settings.MEDIA_URL):]).lstrip('/')
            return None

        validated_urls: list[str] = []
        for u in image_urls:
            storage_path = _storage_path_from_url(u)
            if not storage_path:
                return Response({"image_urls": "Contains disallowed or external URL"}, status=status.HTTP_400_BAD_REQUEST)
            # confirm file exists
            if not default_storage.exists(storage_path):
                return Response({"image_urls": f"Uploaded image not found: {u}"}, status=status.HTTP_400_BAD_REQUEST)
            validated_urls.append(u)

        # All validations passed — create comment and image records
        with transaction.atomic():
            comment = PlaceComment.objects.create(shared_place=shared_place, user=request.user, text=text)
            created_images = []
            for url in validated_urls:
                img = CommentImage.objects.create(comment=comment, user=request.user, image_url=url)
                created_images.append(img)

        comment_data = PlaceCommentSerializer(comment).data
        images_data = CommentImageSerializer(created_images, many=True).data
        return Response({"comment": comment_data, "images": images_data}, status=status.HTTP_201_CREATED)
    
    def get(self, request, mapbox_id):
        """Retrieve comments for a SharedPlace identified by mapbox_id in the URL.

        Endpoint: GET /api/plans/places/by-mapbox/<mapbox_id>/comments/
        Query params: ?limit=<int> (optional, default 50, max 200)
        """
        shared_place = get_object_or_404(SharedPlace, mapbox_id=mapbox_id)

        # optimize related fetches to avoid N+1
        qs = PlaceComment.objects.filter(shared_place=shared_place).select_related('user').prefetch_related('images').order_by('-created_at')

        # simple limit param to avoid returning huge payloads
        try:
            limit = int(request.query_params.get('limit', 50))
        except Exception:
            limit = 50
        limit = max(1, min(limit, 200))

        comments = list(qs[:limit])

        serializer = PlaceCommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class UploadCommentImageAPIView(APIView):
    """Accept multipart file uploads for comment images and return serialized image records.

    Expects files under the 'images' field.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        files = request.FILES.getlist('images')
        if not files:
            return Response({'detail': 'No files uploaded under "images"'}, status=status.HTTP_400_BAD_REQUEST)

        comment_id = request.data.get('comment_id')
        mapbox_id = request.data.get('mapbox_id')

        comment = None
        if comment_id:
            try:
                comment = PlaceComment.objects.get(pk=int(comment_id))
            except Exception:
                return Response({'detail': 'Invalid comment_id'}, status=status.HTTP_400_BAD_REQUEST)

        shared_place = None
        if not comment and mapbox_id:
            try:
                shared_place = SharedPlace.objects.get(mapbox_id=mapbox_id)
            except SharedPlace.DoesNotExist:
                shared_place = None

        urls = []
        # cap a reasonable number per request
        MAX_FILES = 3
        MAX_SIZE = 5 * 1024 * 1024  # 5MB
        for f in files[:MAX_FILES]:
            # server-side validations: mime and size
            content_type = getattr(f, 'content_type', '')
            if not content_type.startswith('image/'):
                return Response({'detail': 'Only image/* files are allowed'}, status=status.HTTP_400_BAD_REQUEST)
            if f.size > MAX_SIZE:
                return Response({'detail': 'Each file must be <= 5MB'}, status=status.HTTP_400_BAD_REQUEST)

            # save file with a uuid prefix to avoid collisions
            # generate a safe filename using uuid + original extension
            _, ext = os.path.splitext(f.name or '')
            name = f"{uuid.uuid4().hex}{ext}"
            path = default_storage.save(f"comment_images/{name}", ContentFile(f.read()))
            image_url = urljoin(settings.MEDIA_URL, path)
            # build absolute URL using request context
            absolute = request.build_absolute_uri(image_url)
            urls.append({'image_url': absolute})

        # Return URLs only; no DB records created. Caller should pass these URLs as image_urls when creating the comment.
        return Response({'images': urls}, status=status.HTTP_201_CREATED)
