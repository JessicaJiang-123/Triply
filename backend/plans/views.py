from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Q
from rest_framework.decorators import action
from django.contrib.auth.models import User
from .services import ai_planner_service, place_service, trip_service, ai_comment_service
from .models import Trip, Day, Place, PlaceComment, CommentImage, SharedPlace
from .serializers import DaySerializer, TripSerializer, PlaceSerializer, PlaceCommentSerializer, CommentImageSerializer

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from urllib.parse import urljoin, urlparse, unquote
import os
import uuid

# Use for other APIView, custom permission to allow owners full access and shared users read-only access
class IsOwnerOrSharedReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # find the related Trip object from Trip, Day, or Place
        trip = None
        if isinstance(obj, Trip):
            trip = obj
        elif hasattr(obj, 'trip'):
            trip = obj.trip
        elif hasattr(obj, 'day'):
            trip = obj.day.trip
        
        if not trip:
            return False

        # allow owner full access
        if trip.user == request.user:
            return True

        # allow shared users read-only access
        if request.user and request.user.is_authenticated:
            is_shared = trip.shared_users.filter(pk=request.user.pk).exists()
            # SAFE_METHODS are GET, HEAD, OPTIONS that do not modify data
            if is_shared and request.method in permissions.SAFE_METHODS:
                return True
        
        return False


class TripViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing the user's trips.
    """
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSharedReadOnly]

    def get_queryset(self):
        """
        This view should return a list of all the trips
        for the currently authenticated user.
        """
        user = self.request.user
        # use Q object to include trips owned by user or shared with user
        return Trip.objects.filter(Q(user=user) | Q(shared_users=user)).distinct().order_by('-created_at')

    @transaction.atomic
    def perform_create(self, serializer):
        validated_data = serializer.validated_data.copy()
        trip = trip_service.create_trip_with_days(user=self.request.user, validated_data=validated_data)
        serializer.instance = trip

    @action(detail=True, methods=['post'], url_path='share')
    def share_trip(self, request, pk=None):
        trip = self.get_object()
        
        # only owner can share the trip
        if trip.user != request.user:
            return Response(
                {"detail": "Only the trip owner can share this plan."},
                status=status.HTTP_403_FORBIDDEN
            )

        email = request.data.get('email')
        if not isinstance(email, str):
            return Response(
                {"detail": "Email must be a string."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # find user by email (iexact = case insensitive)
            user_to_share = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"detail": f"User with email {email} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # prevent sharing with oneself
        if user_to_share == request.user:
            return Response(
                {"detail": "You cannot share a trip with yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # add user to shared_users list
        trip.shared_users.add(user_to_share)
        trip.save()

        # return share UUID
        return Response(
            {
                'message': f'Trip successfully shared with {email}.',
            },
            status=status.HTTP_200_OK
        )


class PlanDetailAPIView(generics.RetrieveAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSharedReadOnly]


class DayForTripAPIView(APIView):
    """
    Retrieve a day for a trip.

    GET: /api/plans/<trip_id>/days/<day_id>/
    """

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSharedReadOnly]

    def get(self, request, trip_id, day_id):
        trip = get_object_or_404(Trip, pk=trip_id)

        # permission check: must be owner
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, trip):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )

        day_obj = get_object_or_404(Day, pk=day_id, trip=trip)
        serializer = DaySerializer(day_obj, context={'request': request})
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

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSharedReadOnly]

    @transaction.atomic
    def post(self, request, trip_id, day_id, place_id=None):
        """
        Create a new place for the specified day, or update an existing place
        if place_id is provided.
        """
        # validate request data
        serializer = PlaceSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        _, day_obj = place_service.get_trip_and_day_for_user(trip_id, day_id, request.user)

        # If place_id is provided -> UPDATE instead of CREATE
        if place_id:
            place = place_service.update_place_for_day(request.data.copy(), day_obj, place_id)
            status_code = status.HTTP_200_OK
        else:
            place = place_service.create_place_for_day(request.data.copy(), day_obj)
            status_code = status.HTTP_201_CREATED
        
        return Response(PlaceSerializer(place, context={'request': request}).data, status=status_code)

    def get(self, request, trip_id, day_id, place_id):
        """
        Retrieve a specific place for the specified day
        """
        _, day_obj = place_service.get_trip_and_day_for_user(trip_id, day_id, request.user)

        place = get_object_or_404(Place, pk=place_id, day=day_obj)
        serializer = PlaceSerializer(place, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, trip_id, day_id, place_id):
        """
        Delete a specific place for the specified day
        """
        _, day_obj = place_service.get_trip_and_day_for_user(trip_id, day_id, request.user)
        remaining_places = place_service.delete_place_for_day(day_obj, place_id)
        serializer = PlaceSerializer(remaining_places, many=True, context={'request': request})
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
        input_serializer = TripSerializer(data=request.data, context={'request': request})
        if not input_serializer.is_valid():
            return Response({"detail": input_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        trip, error_message = ai_planner_service.create_trip_plan_from_ai(request.user, input_serializer.validated_data)

        if not trip:
            return Response(
                {"detail": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
                
        output_serializer = TripSerializer(trip, context={'request': request})

        return Response(
            output_serializer.data,
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
        if len(image_urls) > 4:
            return Response({"image_urls": "You can upload a maximum of 4 images per comment."}, status=status.HTTP_400_BAD_REQUEST)

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
        MAX_FILES = 4
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
    

@api_view(["GET"])
def generate_trip_comments_view(request, trip_id):

    comment_results, error_message = ai_comment_service.ai_auto_generate_comments(trip_id)

    if not comment_results and error_message:
        return Response(
            {"detail": error_message},
            status=status.HTTP_400_BAD_REQUEST
        )
    else:
        return Response(
            comment_results,
            status=status.HTTP_200_OK
        )
