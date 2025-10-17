"""Serializers for skate spots."""

from rest_framework import serializers

from .models import SkateSpot


class LocationSerializer(serializers.Serializer):
    """Serializer for location data."""

    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    city = serializers.CharField(min_length=1)
    country = serializers.CharField(min_length=1)


class SkateSpotSerializer(serializers.ModelSerializer):
    """Serializer for SkateSpot model."""

    location = serializers.SerializerMethodField()
    owner_id = serializers.UUIDField(source="owner.id", read_only=True)

    class Meta:
        model = SkateSpot
        fields = (
            "id",
            "name",
            "description",
            "spot_type",
            "difficulty",
            "location",
            "is_public",
            "requires_permission",
            "owner_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "owner_id")

    def get_location(self, obj):
        """Return location as a nested dict."""
        return {
            "latitude": obj.latitude,
            "longitude": obj.longitude,
            "address": obj.address,
            "city": obj.city,
            "country": obj.country,
        }


class SkateSpotCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating skate spots - accepts both nested and flat data."""

    location = LocationSerializer(required=False)
    # Also accept flat location fields for form submissions
    latitude = serializers.FloatField(min_value=-90, max_value=90, required=False, write_only=True)
    longitude = serializers.FloatField(
        min_value=-180, max_value=180, required=False, write_only=True
    )
    city = serializers.CharField(required=False, write_only=True)
    country = serializers.CharField(required=False, write_only=True)
    address = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = SkateSpot
        fields = (
            "name",
            "description",
            "spot_type",
            "difficulty",
            "location",
            "latitude",
            "longitude",
            "city",
            "country",
            "address",
            "is_public",
            "requires_permission",
        )

    def create(self, validated_data):
        """Create a skate spot with nested or flat location data."""
        # Check if location is nested (JSON) or flat (form data)
        if "location" in validated_data:
            location_data = validated_data.pop("location")
        else:
            # Extract flat location fields
            required_fields = ["latitude", "longitude", "city", "country"]
            missing_fields = [field for field in required_fields if field not in validated_data]

            if missing_fields:
                raise serializers.ValidationError(
                    {
                        field: "This field is required when 'location' is not provided."
                        for field in missing_fields
                    }
                )

            location_data = {field: validated_data.pop(field) for field in required_fields}
            location_data["address"] = validated_data.pop("address", "")

        spot = SkateSpot.objects.create(
            **validated_data,
            latitude=location_data["latitude"],
            longitude=location_data["longitude"],
            city=location_data["city"],
            country=location_data["country"],
            address=location_data.get("address", ""),
        )
        return spot


class SkateSpotUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating skate spots - accepts both nested and flat data."""

    location = LocationSerializer(required=False)
    # Also accept flat location fields for form submissions
    latitude = serializers.FloatField(min_value=-90, max_value=90, required=False, write_only=True)
    longitude = serializers.FloatField(
        min_value=-180, max_value=180, required=False, write_only=True
    )
    city = serializers.CharField(required=False, write_only=True)
    country = serializers.CharField(required=False, write_only=True)
    address = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = SkateSpot
        fields = (
            "name",
            "description",
            "spot_type",
            "difficulty",
            "location",
            "latitude",
            "longitude",
            "city",
            "country",
            "address",
            "is_public",
            "requires_permission",
        )

    def update(self, instance, validated_data):
        """Update a skate spot with optional nested or flat location data."""
        # Check if location is nested (JSON) or flat (form data)
        if "location" in validated_data:
            location_data = validated_data.pop("location")
        elif any(key in validated_data for key in ["latitude", "longitude", "city", "country"]):
            # Extract flat location fields if any are present
            location_data = {}
            for field in ["latitude", "longitude", "city", "country", "address"]:
                if field in validated_data:
                    location_data[field] = validated_data.pop(field)
        else:
            location_data = None

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update location fields if provided
        if location_data:
            instance.latitude = location_data.get("latitude", instance.latitude)
            instance.longitude = location_data.get("longitude", instance.longitude)
            instance.city = location_data.get("city", instance.city)
            instance.country = location_data.get("country", instance.country)
            instance.address = location_data.get("address", instance.address)

        instance.save()
        return instance


class GeoJSONPointSerializer(serializers.Serializer):
    """Serializer for GeoJSON Point geometry."""

    type = serializers.CharField(default="Point")
    coordinates = serializers.ListField(child=serializers.FloatField(), min_length=2, max_length=2)


class GeoJSONFeaturePropertiesSerializer(serializers.Serializer):
    """Serializer for GeoJSON feature properties."""

    id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
    spot_type = serializers.CharField()
    difficulty = serializers.CharField()
    city = serializers.CharField()
    country = serializers.CharField()
    address = serializers.CharField(allow_null=True)
    is_public = serializers.BooleanField()
    requires_permission = serializers.BooleanField()


class GeoJSONFeatureSerializer(serializers.Serializer):
    """Serializer for a GeoJSON Feature."""

    type = serializers.CharField(default="Feature")
    geometry = GeoJSONPointSerializer()
    properties = GeoJSONFeaturePropertiesSerializer()


class GeoJSONFeatureCollectionSerializer(serializers.Serializer):
    """Serializer for a GeoJSON FeatureCollection."""

    type = serializers.CharField(default="FeatureCollection")
    features = GeoJSONFeatureSerializer(many=True)
