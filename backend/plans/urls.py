from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'trips', views.TripViewSet, basename='trip')

urlpatterns = [
     # Get a specific day for a trip
     path("trips/<int:trip_id>/days/<int:day_id>/",
          views.DayForTripAPIView.as_view(), name="day-detail"),
     # Create a place for a day
     path("trips/<int:trip_id>/days/<int:day_id>/places/",
          views.PlaceForDayAPIView.as_view(), name="place-create"),
     # Get or Update or Delete a specific place for a day
     path("trips/<int:trip_id>/days/<int:day_id>/places/<int:place_id>/",
          views.PlaceForDayAPIView.as_view(), name="place-detail"),

     # Comments by mapbox_id
     path("places/by-mapbox/<str:mapbox_id>/comments/",
          views.PlaceCommentAPIView.as_view(), name="place-comments-by-mapbox"),

     # Upload comment images (multipart/form-data)
     path("comments/upload-images/", views.UploadCommentImageAPIView.as_view(), name="upload-comment-images"),

     # Lightweight preview: return recent comment images for a shared place via mapbox_id
     path("places/by-mapbox/<str:mapbox_id>/comment-images/",
          views.PlaceCommentImagesAPIView.as_view(), name="place-comment-images"),
     
     # Register the trips router URLs
     path("", include(router.urls)),

     # AI-generated plan
     path(
        'generate-ai-plan/',
        views.AIGeneratePlanView.as_view(), 
        name='generate-ai-plan'
    ),
]
