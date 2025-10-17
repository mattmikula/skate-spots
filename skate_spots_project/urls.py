"""URL configuration for skate_spots_project project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from accounts.frontend_views import login_page, logout_view, register_page
from spots.frontend_views import (
    edit_spot,
    home,
    list_spots,
    map_view,
    new_spot,
    rating_form,
    spot_detail,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Frontend HTML pages
    path("", home, name="home"),
    path("skate-spots/", list_spots, name="list_spots"),
    path("skate-spots/new/", new_spot, name="new_spot"),
    path("skate-spots/<uuid:spot_id>/", spot_detail, name="spot_detail"),
    path("skate-spots/<uuid:spot_id>/edit/", edit_spot, name="edit_spot"),
    path("skate-spots/<uuid:spot_id>/rating-form/", rating_form, name="rating_form"),
    path("map/", map_view, name="map"),
    path("login/", login_page, name="login"),
    path("register/", register_page, name="register"),
    path("logout/", logout_view, name="logout"),
    # API endpoints
    path("api/v1/", include("accounts.urls")),
    path("api/v1/", include("spots.urls")),
    path("api/v1/", include("ratings.urls")),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
