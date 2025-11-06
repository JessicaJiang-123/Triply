from django.urls import path
from . import views

urlpatterns = [
    path("<int:pk>/", views.PlanDetailAPIView.as_view(), name="plan-detail"),
    path("share/<uuid:share_uuid>/",
         views.PlanShareAPIView.as_view(), name="plan-share"),

    # Create place for a day (POST) and delete a place (DELETE with place_id)
    path("<int:trip_id>/days/<int:day_id>/places/",
         views.PlaceForDayAPIView.as_view(), name="place-create"),
    path("<int:trip_id>/days/<int:day_id>/places/<int:place_id>/",
         views.PlaceForDayAPIView.as_view(), name="place-delete"),
]
