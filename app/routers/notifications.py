"""API endpoints for user notifications."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.db.models import UserORM  # noqa: TCH001
from app.models.notification import (
    Notification,
    NotificationBulkUpdateResult,
    NotificationListResponse,
    NotificationUnreadCount,
)
from app.services.notification_service import NotificationService, get_notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    current_user: Annotated[UserORM, Depends(get_current_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
    limit: int = 20,
    offset: int = 0,
    include_read: bool = True,
) -> NotificationListResponse:
    """Return notifications for the authenticated user."""

    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    return notification_service.list_notifications(
        str(current_user.id),
        include_read=include_read,
        limit=limit,
        offset=offset,
    )


@router.get("/unread-count", response_model=NotificationUnreadCount)
async def get_unread_count(
    current_user: Annotated[UserORM, Depends(get_current_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
) -> NotificationUnreadCount:
    """Return the user's unread notification count."""

    return notification_service.unread_count(str(current_user.id))


@router.post("/{notification_id}/read", response_model=Notification)
async def mark_notification_read(
    notification_id: UUID,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
) -> Notification:
    """Mark a single notification as read."""

    notification = notification_service.mark_as_read(str(notification_id), str(current_user.id))
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notification


@router.post("/mark-all-read", response_model=NotificationBulkUpdateResult)
async def mark_all_notifications_read(
    current_user: Annotated[UserORM, Depends(get_current_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
) -> NotificationBulkUpdateResult:
    """Mark all unread notifications as read."""

    return notification_service.mark_all_as_read(str(current_user.id))
