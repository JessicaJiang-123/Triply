from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def user_profile(request):
    google_user = request.user.social_auth.get(provider="google-oauth2")
    extra_data = google_user.extra_data if google_user else {}

    return JsonResponse({
        "is_authenticated": True,
        "username": request.user.get_full_name() or request.user.username,
        "email": request.user.email,
        "picture": extra_data.get("picture"),
    })
