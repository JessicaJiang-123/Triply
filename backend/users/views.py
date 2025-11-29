import requests
import uuid
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.core.files.base import ContentFile
from .models import UserProfile

def user_profile(request):
    if not request.user.is_authenticated:
        return JsonResponse({"is_authenticated": False})

    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=400)
    
    google_user = request.user.social_auth.filter(provider="google-oauth2").first()
    extra_data = google_user.extra_data if google_user else {}

    # Save or update user profile with Google avatar URL
    google_avatar_url = extra_data.get("picture")
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if google_avatar_url and (not profile.google_avatar_url or profile.google_avatar_url != google_avatar_url):
        profile.google_avatar_url = google_avatar_url
        try:
            r = requests.get(google_avatar_url, timeout=5)
            if r.status_code == 200 and r.headers.get('Content-Type', '').startswith('image/'):
                MAX_BYTES = 200 * 1024  # 200 KB
                content = r.content[:MAX_BYTES]
                if content:
                    fname = f'{uuid.uuid4().hex}.jpg'
                    profile.avatar.save(fname, ContentFile(content), save=False)
        except Exception:
            # ignore errors during avatar fetch; keep google_avatar_url for later use
            pass
        profile.save()

    return JsonResponse({
        "is_authenticated": True,
        "id": request.user.id,
        "username": request.user.get_full_name() or request.user.username,
        "email": request.user.email,
        "picture": google_avatar_url,
    })

def user_logout(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "User not authenticated"}, status=401)

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    logout(request)
    return JsonResponse({"success": True, "message": "Logged out successfully"})
