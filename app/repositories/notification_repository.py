"""Repository for persisting user notifications."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from app.db.models import NotificationORM

if TYPE_CHECKING:  # pragma: no cover
    from sqlalchemy.orm import Session


@dataclass(slots=True)
class NotificationCreateData:
    """Payload used when creating notifications."""

    user_id: str
    notification_type: str
    actor_id: str | None = None
    activity_id: str | None = None
    metadata: dict | None = None


class NotificationRepository:
    """Data access helpers for notifications."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: NotificationCreateData) -> NotificationORM:
        """Create a single notification."""

        notification = NotificationORM(
            user_id=payload.user_id,
            actor_id=payload.actor_id,
            activity_id=payload.activity_id,
            notification_type=payload.notification_type,
            notification_metadata=json.dumps(payload.metadata) if payload.metadata else None,
        )
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        return notification

    def bulk_create(self, notifications: list[NotificationCreateData]) -> list[NotificationORM]:
        """Create multiple notifications in one transaction."""

        if not notifications:
            return []

        orm_notifications = [
            NotificationORM(
                user_id=payload.user_id,
                actor_id=payload.actor_id,
                activity_id=payload.activity_id,
                notification_type=payload.notification_type,
                notification_metadata=json.dumps(payload.metadata) if payload.metadata else None,
            )
            for payload in notifications
        ]
        self.session.add_all(orm_notifications)
        self.session.commit()
        for notification in orm_notifications:
            self.session.refresh(notification)
        return orm_notifications

    def list_for_user(
        self,
        user_id: str,
        *,
        include_read: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[NotificationORM], int]:
        """Return notifications for a user ordered by recency."""

        stmt = select(NotificationORM).where(NotificationORM.user_id == user_id)
        count_stmt = select(func.count(NotificationORM.id)).where(
            NotificationORM.user_id == user_id
        )

        if not include_read:
            stmt = stmt.where(NotificationORM.is_read.is_(False))
            count_stmt = count_stmt.where(NotificationORM.is_read.is_(False))

        total = self.session.execute(count_stmt).scalar() or 0

        notifications = (
            self.session.execute(
                stmt.order_by(NotificationORM.created_at.desc()).limit(limit).offset(offset)
            )
            .scalars()
            .all()
        )

        return notifications, total

    def mark_as_read(self, notification_id: str, user_id: str) -> NotificationORM | None:
        """Mark a specific notification as read."""

        notification = (
            self.session.execute(
                select(NotificationORM).where(
                    NotificationORM.id == notification_id,
                    NotificationORM.user_id == user_id,
                )
            )
            .scalars()
            .one_or_none()
        )

        if notification is None:
            return None

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(notification)

        return notification

    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all unread notifications for the user as read."""

        now = datetime.utcnow()
        result = self.session.execute(
            update(NotificationORM)
            .where(
                NotificationORM.user_id == user_id,
                NotificationORM.is_read.is_(False),
            )
            .values(is_read=True, read_at=now)
        )
        self.session.commit()
        return result.rowcount or 0

    def count_unread(self, user_id: str) -> int:
        """Return number of unread notifications."""

        return (
            self.session.execute(
                select(func.count(NotificationORM.id)).where(
                    NotificationORM.user_id == user_id,
                    NotificationORM.is_read.is_(False),
                )
            ).scalar()
            or 0
        )

    def delete_for_activity(self, activity_id: str) -> int:
        """Remove notifications tied to an activity (used when activity is deleted)."""

        result = self.session.execute(
            delete(NotificationORM).where(NotificationORM.activity_id == activity_id)
        )
        self.session.commit()
        return result.rowcount or 0
