from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.user_profile, name="user_profile"),
    path("logout/", views.user_logout, name="user_logout"),
]
