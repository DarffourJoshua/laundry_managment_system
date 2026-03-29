# laundryadmin/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError, AuthenticationFailed


class CookieJWTAuthentication(JWTAuthentication):
    """
    Reads the JWT access token from the HttpOnly cookie
    instead of the Authorization header.
    """
    def authenticate(self, request):
        access_token = request.COOKIES.get('access_token')

        if not access_token:
            return None  # No token — let permission class handle the rejection

        try:
            validated_token = self.get_validated_token(access_token)
            return self.get_user(validated_token), validated_token

        except (InvalidToken, TokenError) as e:
            raise AuthenticationFailed(str(e))