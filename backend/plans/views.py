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


class PlaceCommentCreateAPIView(APIView):
    """Create a comment for a place. Accepts optional image_urls list (<=5).

    Notes:
    - Comments are independent of trip ownership; any authenticated user
      may comment on any place. The trip_id/day_id in the URL are only used
      to locate the target place and validate the URL structure.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, trip_id, day_id, place_id):
        # We do not enforce trip ownership here; any authenticated user can comment.
        day_obj = get_object_or_404(Day, pk=day_id, trip__pk=trip_id)
        place = get_object_or_404(Place, pk=place_id, day=day_obj)

        # Prefer an explicit mapbox_id in the request body so clients can
        # create comments without relying on the place_id lookup.
        mapbox_id = (request.data.get('mapbox_id') or '').strip()
        shared_place = None
        if place.mapbox_id:
            shared_place, _ = SharedPlace.objects.get_or_create(
                mapbox_id=place.mapbox_id,
                defaults={
                    'name': place.name or '',
                    'latitude': place.latitude,
                    'longitude': place.longitude,
                }
            )
        else:
            # If the place doesn't have a mapbox_id, we cannot attach to a shared feature
            return Response({"detail": "Place does not have mapbox_id; cannot attach shared comment."}, status=status.HTTP_400_BAD_REQUEST)

        text = request.data.get('text', '')
        image_urls = request.data.get('image_urls', [])

        # image_urls is optional; validate type early to provide a clear error
        if not isinstance(image_urls, list):
            return Response({"image_urls": "must be a list"}, status=status.HTTP_400_BAD_REQUEST)
        if len(image_urls) > 5:
            # Enforce per-comment image limit to avoid excessive storage/abuse
            return Response({"image_urls": "You can upload a maximum of 5 images per comment."}, status=status.HTTP_400_BAD_REQUEST)

        # Create comment and images in a transaction
        with transaction.atomic():
            comment = PlaceComment.objects.create(shared_place=shared_place, user=request.user, text=text)
            created_images = []
            for url in image_urls:
                img = CommentImage.objects.create(comment=comment, user=request.user, image_url=url)
                created_images.append(img)

            comment_data = PlaceCommentSerializer(comment).data
            images_data = CommentImageSerializer(created_images, many=True).data
            return Response({"comment": comment_data, "images": images_data}, status=status.HTTP_201_CREATED)


class CommentImageUploadAPIView(APIView):
    """Upload (attach) images to an existing comment. Enforces <=5 images per comment.

    Only the original comment author may attach images. Trip ownership is not
    considered here because any authenticated user may comment on any place.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(PlaceComment, pk=comment_id)
        # Only the comment author may attach images to their comment.
        if request.user != comment.user:
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        image_urls = request.data.get('image_urls', [])
        # validate input format
        if not isinstance(image_urls, list):
            return Response({"image_urls": "must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        existing = CommentImage.objects.filter(comment=comment).count()
        # Check aggregate limit (existing + new) to enforce cap
        if existing + len(image_urls) > 5:
            return Response({"detail": "You can upload a maximum of 5 images per comment."}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        with transaction.atomic():
            for url in image_urls:
                img = CommentImage.objects.create(
                    comment=comment, user=request.user, image_url=url)
                created.append(img)

        # Return the newly created image records for client-side display
        return Response(CommentImageSerializer(created, many=True).data, status=status.HTTP_201_CREATED)


class PlaceCommentImagesAPIView(APIView):
    """Return a small set of comment images for a place (for a right-top preview)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, mapbox_id):
        # Directly resolve the SharedPlace from provided mapbox_id
        shared_place = get_object_or_404(SharedPlace, mapbox_id=mapbox_id)
        limit = int(request.query_params.get('limit', 5))
        per_comment = int(request.query_params.get('per_comment', 0))

        if per_comment:
            images = []

            for comment in shared_place.comments.order_by('-created_at'): # type: ignore
                img = comment.images.order_by('-created_at').first()
                if img:
                    images.append(img)
                if len(images) >= limit:
                    break
        else:
            # Return the most recent comment images for the place (global recent)
            images = list(CommentImage.objects.filter(comment__shared_place=shared_place).order_by('-created_at')[:limit])

        return Response(CommentImageSerializer(images, many=True).data, status=status.HTTP_200_OK)


class PlaceCommentCreateByMapboxAPIView(APIView):
    """Create a comment for a SharedPlace identified by mapbox_id in the URL.

    Endpoint: POST /api/plans/places/by-mapbox/<mapbox_id>/comments/
    Payload: { "text": "...", "image_urls": [...], optional other fields }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, mapbox_id):
        shared_place = get_object_or_404(SharedPlace, mapbox_id=mapbox_id)

        text = request.data.get('text', '')
        image_urls = request.data.get('image_urls', [])

        if not isinstance(image_urls, list):
            return Response({"image_urls": "must be a list"}, status=status.HTTP_400_BAD_REQUEST)
        if len(image_urls) > 5:
            return Response({"image_urls": "You can upload a maximum of 5 images per comment."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            comment = PlaceComment.objects.create(shared_place=shared_place, user=request.user, text=text)
            created_images = []
            for url in image_urls:
                img = CommentImage.objects.create(comment=comment, user=request.user, image_url=url)
                created_images.append(img)

        comment_data = PlaceCommentSerializer(comment).data
        images_data = CommentImageSerializer(created_images, many=True).data
        return Response({"comment": comment_data, "images": images_data}, status=status.HTTP_201_CREATED)
