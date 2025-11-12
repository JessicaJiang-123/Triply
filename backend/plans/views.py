from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, permissions, status
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models as dj_models
from django.db import transaction
from django.db.models import F
from datetime import datetime, timedelta
from rest_framework.decorators import action
from .models import Trip, Day, Place, PlaceComment, CommentImage, SharedPlace
from .serializers import DaySerializer, TripSerializer, PlaceSerializer, PlaceCommentSerializer, CommentImageSerializer

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from urllib.parse import urljoin, urlparse
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
                    new_start = datetime.strptime(
                        start_time_str, '%H:%M').time()
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

            # If frontend provided a mapbox_id, link (or create) the SharedPlace
            mapbox_id = data.get('mapbox_id')
            if mapbox_id:
                shared_place, _ = SharedPlace.objects.get_or_create(
                    mapbox_id=mapbox_id,
                    defaults={
                        'name': place.name or '', # type: ignore
                        'latitude': place.latitude, # type: ignore
                        'longitude': place.longitude, # type: ignore
                    }
                )
                place.shared_place = shared_place # type: ignore
                place.mapbox_id = mapbox_id # type: ignore
                place.save() # type: ignore

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

        # If mapbox_id provided and changed, update shared_place accordingly
        if 'mapbox_id' in data:
            new_mapbox = data.get('mapbox_id')
            if new_mapbox:
                if place.mapbox_id != new_mapbox:
                    # Rebind to the new SharedPlace
                    shared_place, _ = SharedPlace.objects.get_or_create(
                        mapbox_id=new_mapbox,
                        defaults={
                            'name': data.get('name', place.name) or '',
                            'latitude': data.get('latitude', place.latitude),
                            'longitude': data.get('longitude', place.longitude),
                        }
                    )
                    place.shared_place = shared_place # type: ignore
                    place.mapbox_id = new_mapbox
            else:
                # if explicitly clearing mapbox_id, unset shared_place
                place.mapbox_id = ''
                place.shared_place = None

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
            if path.startswith(settings.MEDIA_URL):
                # strip leading MEDIA_URL
                storage_path = path[len(settings.MEDIA_URL):].lstrip('/')
                return storage_path
            # also allow bare relative urls starting with MEDIA_URL
            if u.startswith(settings.MEDIA_URL):
                return u[len(settings.MEDIA_URL):].lstrip('/')
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

    Expects files under the 'images' field. Optionally accepts 'comment_id' to attach to an existing
    comment, or 'mapbox_id' to create a new empty comment for the shared place and attach images to it.
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
        MAX_FILES = 5
        MAX_SIZE = 5 * 1024 * 1024  # 5MB
        for f in files[:MAX_FILES]:
            # server-side validations: mime and size
            content_type = getattr(f, 'content_type', '')
            if not content_type.startswith('image/'):
                return Response({'detail': 'Only image/* files are allowed'}, status=status.HTTP_400_BAD_REQUEST)
            if f.size > MAX_SIZE:
                return Response({'detail': 'Each file must be <= 5MB'}, status=status.HTTP_400_BAD_REQUEST)

            # save file with a uuid prefix to avoid collisions
            name = f"{uuid.uuid4().hex}_{f.name}"
            path = default_storage.save(f"comment_images/{name}", ContentFile(f.read()))
            image_url = urljoin(settings.MEDIA_URL, path)
            # build absolute URL using request context
            absolute = request.build_absolute_uri(image_url)
            urls.append({'image_url': absolute})

        # Return URLs only; no DB records created. Caller should pass these URLs as image_urls when creating the comment.
        return Response({'images': urls}, status=status.HTTP_201_CREATED)
    
