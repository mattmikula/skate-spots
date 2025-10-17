"""Views and ViewSets for skate spots."""

import logging

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .filters import SkateSpotFilter
from .models import SkateSpot
from .permissions import IsOwnerOrAdmin
from .serializers import (
    GeoJSONFeatureCollectionSerializer,
    SkateSpotCreateSerializer,
    SkateSpotSerializer,
    SkateSpotUpdateSerializer,
)

logger = logging.getLogger(__name__)


class SkateSpotViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on skate spots."""

    queryset = SkateSpot.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    filterset_class = SkateSpotFilter

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return SkateSpotCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return SkateSpotUpdateSerializer
        return SkateSpotSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == "create":
            return [IsAuthenticated()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticatedOrReadOnly()]

    @method_decorator(ratelimit(key="ip", rate="50/m", method="POST"))
    def create(self, request, *args, **kwargs):
        """Create a new skate spot."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Set the owner to the current user
        spot = serializer.save(owner=request.user)
        logger.info(
            "skate spot created",
            extra={"spot_id": str(spot.id), "owner_id": str(request.user.id)},
        )

        # Return with the read serializer
        return Response(SkateSpotSerializer(spot).data, status=status.HTTP_201_CREATED)

    @method_decorator(ratelimit(key="ip", rate="50/m", method="PUT"))
    def update(self, request, *args, **kwargs):
        """Update a skate spot."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        spot = serializer.save()

        logger.info("skate spot updated", extra={"spot_id": str(spot.id)})

        return Response(SkateSpotSerializer(spot).data)

    @method_decorator(ratelimit(key="ip", rate="50/m", method="DELETE"))
    def destroy(self, request, *args, **kwargs):
        """Delete a skate spot."""
        instance = self.get_object()
        spot_id = str(instance.id)

        self.perform_destroy(instance)
        logger.info("skate spot deleted", extra={"spot_id": spot_id})

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="geojson")
    def geojson(self, request):
        """Return skate spots in GeoJSON format."""
        # Apply filters
        queryset = self.filter_queryset(self.get_queryset())

        # Build GeoJSON features
        features = []
        for spot in queryset:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [spot.longitude, spot.latitude],
                },
                "properties": {
                    "id": str(spot.id),
                    "name": spot.name,
                    "description": spot.description,
                    "spot_type": spot.spot_type,
                    "difficulty": spot.difficulty,
                    "city": spot.city,
                    "country": spot.country,
                    "address": spot.address,
                    "is_public": spot.is_public,
                    "requires_permission": spot.requires_permission,
                },
            }
            features.append(feature)

        geojson_data = {"type": "FeatureCollection", "features": features}

        serializer = GeoJSONFeatureCollectionSerializer(geojson_data)
        return Response(serializer.data)
