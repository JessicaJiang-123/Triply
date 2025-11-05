from django.urls import path
from . import views
from django.urls import include

urlpatterns = [
    path("user/profile/", views.user_profile, name="user_profile"),
    path("user/logout/", views.user_logout, name="user_logout"),
    path("plans/", include("plans.urls")),
]
