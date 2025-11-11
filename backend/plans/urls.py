from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'trips', views.TripViewSet, basename='trip')

urlpatterns = [
     path("share/<uuid:share_uuid>/",
          views.PlanShareAPIView.as_view(), name="plan-share"),

     # Get a specific day for a trip
     path("trips/<int:trip_id>/days/<int:day_id>/",
          views.DayForTripAPIView.as_view(), name="day-detail"),
     # Create a place for a day
     path("trips/<int:trip_id>/days/<int:day_id>/places/",
          views.PlaceForDayAPIView.as_view(), name="place-create"),
     # Get or Update or Delete a specific place for a day
     path("trips/<int:trip_id>/days/<int:day_id>/places/<int:place_id>/",
          views.PlaceForDayAPIView.as_view(), name="place-detail"),
     # Comments: create a comment for a place (optionally with image URLs)
     path("trips/<int:trip_id>/days/<int:day_id>/places/<int:place_id>/comments/",
          views.PlaceCommentCreateAPIView.as_view(), name="place-comment-create"),
     # Create comments by mapbox_id directly (no trip/day/place IDs required)
     path("places/by-mapbox/<str:mapbox_id>/comments/",
          views.PlaceCommentCreateByMapboxAPIView.as_view(), name="place-comment-create-by-mapbox"),

     # Attach images to an existing comment (comment author only)
     path("comments/<int:comment_id>/images/",
          views.CommentImageUploadAPIView.as_view(), name="comment-image-upload"),

     # Lightweight preview: return recent comment images for a shared place via mapbox_id
     path("places/by-mapbox/<str:mapbox_id>/comment-images/",
          views.PlaceCommentImagesAPIView.as_view(), name="place-comment-images"),
     path("", include(router.urls))
]
