"""Views and ViewSets for ratings."""

import logging

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Rating
from .permissions import IsRatingOwnerOrAdmin
from .serializers import (
    RatingCreateSerializer,
    RatingSerializer,
    RatingUpdateSerializer,
)

logger = logging.getLogger(__name__)


class RatingViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on ratings."""

    queryset = Rating.objects.select_related("user", "spot").all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsRatingOwnerOrAdmin]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return RatingCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return RatingUpdateSerializer
        return RatingSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == "create":
            return [IsAuthenticated()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsRatingOwnerOrAdmin()]
        return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        """Filter ratings by spot if specified."""
        queryset = super().get_queryset()
        spot_id = self.request.query_params.get("spot")
        if spot_id:
            queryset = queryset.filter(spot_id=spot_id)
        return queryset

    @method_decorator(ratelimit(key="ip", rate="50/m", method="POST"))
    def create(self, request, *args, **kwargs):  # noqa: ARG002
        """Create a new rating."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check if user has already rated this spot
        spot = serializer.validated_data["spot"]
        if Rating.objects.filter(spot=spot, user=request.user).exists():
            return Response(
                {"detail": "You have already rated this spot"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set the user to the current user
        rating = serializer.save(user=request.user)
        logger.info(
            "rating created",
            extra={
                "rating_id": str(rating.id),
                "user_id": str(request.user.id),
                "spot_id": str(rating.spot.id),
            },
        )

        # Return with the read serializer
        return Response(RatingSerializer(rating).data, status=status.HTTP_201_CREATED)

    @method_decorator(ratelimit(key="ip", rate="50/m", method="PUT"))
    def update(self, request, *args, **kwargs):  # noqa: ARG002
        """Update a rating."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        rating = serializer.save()

        logger.info("rating updated", extra={"rating_id": str(rating.id)})

        return Response(RatingSerializer(rating).data)

    @method_decorator(ratelimit(key="ip", rate="50/m", method="DELETE"))
    def destroy(self, request, *args, **kwargs):  # noqa: ARG002
        """Delete a rating."""
        instance = self.get_object()
        rating_id = str(instance.id)

        self.perform_destroy(instance)
        logger.info("rating deleted", extra={"rating_id": rating_id})

        return Response(status=status.HTTP_204_NO_CONTENT)
