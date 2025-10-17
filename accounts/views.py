"""Authentication views and viewsets."""

import logging

from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    LoginSerializer,
    TokenSerializer,
    UserCreateSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.GenericViewSet):
    """ViewSet for authentication operations."""

    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST"))
    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        """Register a new user."""
        logger.info("registration attempt", extra={"username": request.data.get("username")})

        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check if user already exists
        if User.objects.filter(email=serializer.validated_data["email"]).exists():
            logger.warning(
                "registration email already exists",
                extra={"email": serializer.validated_data["email"]},
            )
            return Response(
                {"detail": "Email already registered"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=serializer.validated_data["username"]).exists():
            logger.warning(
                "registration username already exists",
                extra={"username": serializer.validated_data["username"]},
            )
            return Response(
                {"detail": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.save()
        logger.info(
            "user registered",
            extra={"user_id": str(user.id), "username": user.username},
        )

        user_serializer = UserSerializer(user)
        return Response(user_serializer.data, status=status.HTTP_201_CREATED)

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST"))
    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request):
        """Login and receive an access token."""
        logger.info("login attempt", extra={"username": request.data.get("username")})

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=username, password=password)

        if user is None:
            logger.warning(
                "login failed",
                extra={"username": username, "reason": "invalid_credentials"},
            )
            return Response(
                {"detail": "Incorrect username or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            logger.warning("login failed", extra={"username": username, "reason": "inactive_user"})
            return Response({"detail": "Inactive user"}, status=status.HTTP_403_FORBIDDEN)

        # Create JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Set token in httponly cookie
        response = Response(TokenSerializer({"access_token": access_token}).data)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="Lax",
            max_age=1800,  # 30 minutes
        )

        logger.info(
            "login successful",
            extra={"user_id": str(user.id), "username": user.username},
        )
        return response

    @action(
        detail=False,
        methods=["post"],
        url_path="logout",
        permission_classes=[IsAuthenticated],
    )
    def logout(self, request):
        """Logout by clearing the access token cookie."""
        logger.info("logout successful")
        response = Response({"message": "Successfully logged out"})
        response.delete_cookie("access_token")
        return response

    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """Get current user information."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
