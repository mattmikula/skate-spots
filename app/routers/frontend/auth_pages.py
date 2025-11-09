"""Authentication page routers (login/register)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.dependencies import get_optional_user
from app.db.models import UserORM  # noqa: TCH001
from app.routers.frontend._shared import templates

router = APIRouter(tags=["frontend"])


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
