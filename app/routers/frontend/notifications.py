"""Notification widget routers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.core.dependencies import get_current_user, get_optional_user
from app.db.models import UserORM  # noqa: TCH001
from app.routers.frontend._shared import _render_notification_widget
from app.services.notification_service import (
    NotificationService,
    get_notification_service,
)



router = APIRouter(tags=["frontend"])


@router.get("/notifications/widget", response_class=HTMLResponse)
async def notifications_widget(
    request: Request,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
) -> HTMLResponse:
    """Return the notification widget for the navigation bar."""
    if current_user is None:
        return HTMLResponse('<div id="notification-widget"></div>')

    return _render_notification_widget(request, current_user, notification_service)


@router.post("/notifications/mark-all", response_class=HTMLResponse)
async def notifications_mark_all(
    request: Request,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
) -> HTMLResponse:
    """Handle mark-all-read actions from the widget."""
    notification_service.mark_all_as_read(str(current_user.id))
    return _render_notification_widget(request, current_user, notification_service)


@router.post("/notifications/{notification_id}/read", response_class=HTMLResponse)
async def notifications_mark_read(
    request: Request,
    notification_id: UUID,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
) -> HTMLResponse:
    """Mark a single notification as read and refresh the widget."""
    notification_service.mark_as_read(str(notification_id), str(current_user.id))
    return _render_notification_widget(request, current_user, notification_service)
