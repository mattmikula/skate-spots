"""Frontend HTML views for skate spots."""

from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render

from ratings.models import Rating

from .forms import SkateSpotForm
from .models import SkateSpot


def home(request):
    """Display home page with all skate spots."""
    spots = (
        SkateSpot.objects.all()
        .select_related("owner")
        .annotate(average_rating=Avg("ratings__score"))
    )
    return render(request, "spots/index.html", {"spots": spots, "user": request.user})


def list_spots(request):
    """Display all skate spots."""
    spots = (
        SkateSpot.objects.all()
        .select_related("owner")
        .annotate(average_rating=Avg("ratings__score"))
    )
    return render(request, "spots/index.html", {"spots": spots, "user": request.user})


@login_required
def new_spot(request):
    """Display form to create a new skate spot."""
    if request.method == "POST":
        form = SkateSpotForm(request.POST)
        if form.is_valid():
            spot = form.save(commit=False)
            spot.owner = request.user
            spot.save()
            return redirect("home")
    else:
        form = SkateSpotForm()

    return render(
        request,
        "spots/spot_form.html",
        {"form": form, "spot": None, "user": request.user},
    )


@login_required
def edit_spot(request, spot_id):
    """Display form to edit an existing skate spot."""
    spot = get_object_or_404(SkateSpot, id=spot_id)

    # Check if user owns the spot or is admin
    if not request.user.is_admin and spot.owner != request.user:
        return redirect("home")

    if request.method == "POST":
        form = SkateSpotForm(request.POST, instance=spot)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = SkateSpotForm(instance=spot)

    return render(
        request,
        "spots/spot_form.html",
        {"form": form, "spot": spot, "user": request.user},
    )


def map_view(request):
    """Display interactive map of all skate spots."""
    return render(request, "spots/map.html", {"user": request.user})


def spot_detail(request, spot_id):
    """Display detailed view of a single spot with ratings."""
    spot = get_object_or_404(SkateSpot, id=spot_id)

    # Get all ratings for this spot
    ratings = Rating.objects.filter(spot=spot).select_related("user")

    # Calculate average rating
    avg_rating = ratings.aggregate(avg=Avg("score"))["avg"]
    spot.average_rating = avg_rating

    # Check if current user has rated this spot
    user_rating = None
    if request.user.is_authenticated:
        user_rating = ratings.filter(user=request.user).first()

    return render(
        request,
        "spots/spot_detail.html",
        {
            "spot": spot,
            "ratings": ratings,
            "average_rating": avg_rating,
            "user_rating": user_rating,
            "user": request.user,
        },
    )


def rating_form(request, spot_id):
    """Display rating form or edit form for a spot."""
    spot = get_object_or_404(SkateSpot, id=spot_id)

    if not request.user.is_authenticated:
        return redirect("login")

    # Check if user has already rated this spot
    user_rating = Rating.objects.filter(spot=spot, user=request.user).first()

    return render(
        request,
        "spots/rating_edit.html",
        {
            "spot": spot,
            "rating": user_rating,
            "user": request.user,
        },
    )
