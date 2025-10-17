"""Frontend HTML endpoints for skate spots."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.dependencies import get_optional_user
from app.db.models import UserORM
from app.services.rating_service import (
    RatingService,
    get_rating_service,
)
from app.services.skate_spot_service import (
    SkateSpotService,
    get_skate_spot_service,
)

router = APIRouter(tags=["frontend"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display home page with all skate spots."""
    spots = service.list_spots()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "spots": spots, "current_user": current_user},
    )


@router.get("/skate-spots", response_class=HTMLResponse)
async def list_spots_page(
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display all skate spots."""
    spots = service.list_spots()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "spots": spots, "current_user": current_user},
    )


@router.get("/skate-spots/new", response_class=HTMLResponse)
async def new_spot_page(
    request: Request,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display form to create a new skate spot."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "spot_form.html",
        {"request": request, "spot": None, "current_user": current_user},
    )


@router.get("/skate-spots/{spot_id}/edit", response_class=HTMLResponse)
async def edit_spot_page(
    request: Request,
    spot_id: UUID,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display form to edit an existing skate spot."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    spot = service.get_spot(spot_id)
    if not spot:
        return RedirectResponse(url="/", status_code=303)

    # Check if user owns the spot or is admin
    if not current_user.is_admin and not service.is_owner(spot_id, current_user.id):
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "spot_form.html",
        {"request": request, "spot": spot, "current_user": current_user},
    )


@router.get("/skate-spots/{spot_id}", response_class=HTMLResponse)
async def spot_detail_page(
    request: Request,
    spot_id: UUID,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    rating_service: Annotated[RatingService, Depends(get_rating_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display details of a specific skate spot with ratings."""
    spot = service.get_spot(spot_id)
    if not spot:
        return RedirectResponse(url="/", status_code=303)

    # Get ratings and user's rating if authenticated
    ratings = rating_service.get_spot_ratings(spot_id)
    user_rating = None
    if current_user:
        user_rating = rating_service.get_user_rating_for_spot(spot_id, current_user.id)

    return templates.TemplateResponse(
        "spot_detail.html",
        {
            "request": request,
            "spot": spot,
            "ratings": ratings,
            "user_rating": user_rating,
            "current_user": current_user,
        },
    )


@router.get("/map", response_class=HTMLResponse)
async def map_view(
    request: Request,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display interactive map of all skate spots."""
    return templates.TemplateResponse(
        "map.html",
        {"request": request, "current_user": current_user},
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display login page."""
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "current_user": None},
    )


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display registration page."""
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "current_user": None},
    )
