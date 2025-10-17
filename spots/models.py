"""Skate spot models."""

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SpotType(models.TextChoices):
    """Types of skate spots."""

    STREET = "street", "Street"
    PARK = "park", "Park"
    SKATEPARK = "skatepark", "Skatepark"
    BOWL = "bowl", "Bowl"
    VERT = "vert", "Vert"
    MINI_RAMP = "mini_ramp", "Mini Ramp"
    STAIRS = "stairs", "Stairs"
    RAIL = "rail", "Rail"
    LEDGE = "ledge", "Ledge"
    GAP = "gap", "Gap"
    OTHER = "other", "Other"


class Difficulty(models.TextChoices):
    """Difficulty levels for skate spots."""

    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"
    EXPERT = "expert", "Expert"


class SkateSpot(models.Model):
    """Model representing a skateboarding spot."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    spot_type = models.CharField(max_length=50, choices=SpotType.choices)
    difficulty = models.CharField(max_length=50, choices=Difficulty.choices)

    # Location fields
    latitude = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    # Access information
    is_public = models.BooleanField(default=True)
    requires_permission = models.BooleanField(default=False)

    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skate_spots",
        db_column="user_id",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "skate_spots"
        verbose_name = "skate spot"
        verbose_name_plural = "skate spots"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["city"]),
            models.Index(fields=["country"]),
            models.Index(fields=["spot_type"]),
            models.Index(fields=["difficulty"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.city}, {self.country})"
