from django.urls import path
from . import views

urlpatterns = [
    path("user/profile/", views.user_profile, name="user_profile"),
    path("user/logout/", views.user_logout, name="user_logout"),
]
