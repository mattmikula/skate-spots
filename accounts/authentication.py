"""Custom authentication classes."""

from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTCookieAuthentication(JWTAuthentication):
    """JWT authentication using cookies."""

    def authenticate(self, request):
        """Extract JWT token from cookie if not in Authorization header."""
        # First try the standard header-based authentication
        header_auth = super().authenticate(request)
        if header_auth is not None:
            return header_auth

        # If no header, try to get token from cookie
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
