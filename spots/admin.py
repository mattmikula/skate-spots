"""Admin configuration for spots app."""

from django.contrib import admin

from .models import SkateSpot


@admin.register(SkateSpot)
class SkateSpotAdmin(admin.ModelAdmin):
    """Admin configuration for SkateSpot model."""

    list_display = (
        "name",
        "city",
        "country",
        "spot_type",
        "difficulty",
        "owner",
        "created_at",
    )
    list_filter = (
        "spot_type",
        "difficulty",
        "is_public",
        "requires_permission",
        "city",
        "country",
    )
    search_fields = ("name", "description", "city", "country")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "description", "spot_type", "difficulty")},
        ),
        (
            "Location",
            {"fields": ("latitude", "longitude", "address", "city", "country")},
        ),
        ("Access", {"fields": ("is_public", "requires_permission")}),
        ("Ownership", {"fields": ("owner",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
