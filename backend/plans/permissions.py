from rest_framework import permissions
from .models import ShareLink, Trip

class CanAccessTrip(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        
        # find the related Trip object
        trip = None
        if isinstance(obj, Trip):
            trip = obj
        elif hasattr(obj, 'trip'):
            trip = obj.trip
        elif hasattr(obj, 'day'):
            trip = obj.day.trip
        if not trip:
            return False

        # Check 1: Authenticated user who owns the trip
        if request.user and request.user.is_authenticated:
            if trip.user == request.user:
                return True

        # Check 2: ShareLink authentication
        if request.auth and isinstance(request.auth, ShareLink):
            share_link = request.auth
            
            if share_link.trip == trip:
                if share_link.permission_level == 'edit':
                    return True 
                if share_link.permission_level == 'read':
                    return request.method in permissions.SAFE_METHODS 
        
        return False