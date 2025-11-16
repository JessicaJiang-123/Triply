from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import ShareLink

class ShareLinkAuthentication(BaseAuthentication):
    def authenticate(self, request):
        
        # get the share token from request headers
        share_token = request.headers.get('X-Share-Token')

        # check if the token exists
        if not share_token:
            return None

        # try to retrieve the ShareLink using the provided token
        try:
            share_link = ShareLink.objects.select_related('trip').get(uuid=share_token)
        except ShareLink.DoesNotExist:
            raise AuthenticationFailed('Invalid share token')
        
        return (None, share_link)