"""Filters for skate spots."""

from django.db.models import Q
import django_filters

from .models import Difficulty, SkateSpot, SpotType


class SkateSpotFilter(django_filters.FilterSet):
    """Filter for skate spots with support for multiple query parameters."""

    search = django_filters.CharFilter(method="filter_search", label="Search")
    spot_type = django_filters.MultipleChoiceFilter(
        choices=SpotType.choices, field_name="spot_type"
    )
    difficulty = django_filters.MultipleChoiceFilter(
        choices=Difficulty.choices, field_name="difficulty"
    )
    city = django_filters.CharFilter(field_name="city", lookup_expr="iexact")
    country = django_filters.CharFilter(field_name="country", lookup_expr="iexact")
    is_public = django_filters.BooleanFilter(field_name="is_public")
    requires_permission = django_filters.BooleanFilter(field_name="requires_permission")

    class Meta:
        model = SkateSpot
        fields = [
            "search",
            "spot_type",
            "difficulty",
            "city",
            "country",
            "is_public",
            "requires_permission",
        ]

    def filter_search(self, queryset, name, value):
        """Filter by search term across multiple fields."""
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(city__icontains=value)
            | Q(country__icontains=value)
        )
