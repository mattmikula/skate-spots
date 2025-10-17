"""URL configuration for spots app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SkateSpotViewSet

router = DefaultRouter()
router.register(r"skate-spots", SkateSpotViewSet, basename="skate-spot")

urlpatterns = [
    path("", include(router.urls)),
]
