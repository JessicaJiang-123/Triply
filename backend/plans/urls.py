from django.urls import path
from . import views

urlpatterns = [
    path("<int:pk>/", views.PlanDetailAPIView.as_view(), name="plan-detail"),
    path("share/<uuid:share_uuid>/",
         views.PlanShareAPIView.as_view(), name="plan-share"),

    # Get a specific day for a trip
    path("<int:trip_id>/days/<int:day_id>/",
         views.DayForTripAPIView.as_view(), name="day-detail"),
    # Create a place for a day
    path("<int:trip_id>/days/<int:day_id>/places/",
         views.PlaceForDayAPIView.as_view(), name="place-create"),
    # Get or Update or Delete a specific place for a day
    path("<int:trip_id>/days/<int:day_id>/places/<int:place_id>/",
         views.PlaceForDayAPIView.as_view(), name="place-detail"),
]
