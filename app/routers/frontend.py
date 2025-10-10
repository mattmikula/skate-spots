"""Frontend HTML endpoints for skate spots."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

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
) -> HTMLResponse:
    """Display home page with all skate spots."""
    spots = service.list_spots()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "spots": spots},
    )


@router.get("/skate-spots", response_class=HTMLResponse)
async def list_spots_page(
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
) -> HTMLResponse:
    """Display all skate spots."""
    spots = service.list_spots()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "spots": spots},
    )


@router.get("/skate-spots/new", response_class=HTMLResponse)
async def new_spot_page(request: Request) -> HTMLResponse:
    """Display form to create a new skate spot."""
    return templates.TemplateResponse(
        "spot_form.html",
        {"request": request, "spot": None},
    )


@router.get("/skate-spots/{spot_id}/edit", response_class=HTMLResponse)
async def edit_spot_page(
    request: Request,
    spot_id: UUID,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
) -> HTMLResponse:
    """Display form to edit an existing skate spot."""
    spot = service.get_spot(spot_id)
    return templates.TemplateResponse(
        "spot_form.html",
        {"request": request, "spot": spot},
    )


@router.get("/map", response_class=HTMLResponse)
async def map_view(request: Request) -> HTMLResponse:
    """Display interactive map of all skate spots."""
    return templates.TemplateResponse(
        "map.html",
        {"request": request},
    )
