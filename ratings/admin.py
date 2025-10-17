"""Admin configuration for ratings."""

from django.contrib import admin

from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Admin interface for Rating model."""

    list_display = ("id", "user", "spot", "score", "created_at")
    list_filter = ("score", "created_at")
    search_fields = ("user__username", "spot__name", "comment")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
