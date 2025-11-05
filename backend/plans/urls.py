from django.urls import path
from . import views

urlpatterns = [
    path("<int:pk>/", views.PlanDetailAPIView.as_view(), name="plan-detail"),
    path("share/<uuid:share_uuid>/",
         views.PlanShareAPIView.as_view(), name="plan-share"),

    path("<int:trip_id>/days/<int:day_id>/places/",
         views.PlaceCreateForDayAPIView.as_view(), name="place-create"),
]
