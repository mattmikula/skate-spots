"""Serializers for ratings."""

from rest_framework import serializers

from .models import Rating


class RatingSerializer(serializers.ModelSerializer):
    """Serializer for Rating model."""

    user_username = serializers.CharField(source="user.username", read_only=True)
    spot_name = serializers.CharField(source="spot.name", read_only=True)

    class Meta:
        model = Rating
        fields = (
            "id",
            "spot",
            "spot_name",
            "user",
            "user_username",
            "score",
            "comment",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at")

    def validate_score(self, value):
        """Validate score is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Score must be between 1 and 5")
        return value


class RatingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ratings."""

    class Meta:
        model = Rating
        fields = ("spot", "score", "comment")

    def validate_score(self, value):
        """Validate score is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Score must be between 1 and 5")
        return value


class RatingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating ratings."""

    class Meta:
        model = Rating
        fields = ("score", "comment")

    def validate_score(self, value):
        """Validate score is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Score must be between 1 and 5")
        return value
