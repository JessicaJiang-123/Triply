from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse

def user_profile(request):
    if not request.user.is_authenticated:
        return JsonResponse({"is_authenticated": False})

    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=400)
    
    google_user = request.user.social_auth.filter(provider="google-oauth2").first()
    extra_data = google_user.extra_data if google_user else {}

    return JsonResponse({
        "id": request.user.id,
        "is_authenticated": True,
        "username": request.user.get_full_name() or request.user.username,
        "email": request.user.email,
        "picture": extra_data.get("picture"),
    })

def user_logout(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "User not authenticated"}, status=401)

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    logout(request)
    return JsonResponse({"success": True, "message": "Logged out successfully"})
