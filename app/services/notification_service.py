"""Service layer for delivering notifications to users."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from fastapi import Depends

from app.core.dependencies import get_db
from app.core.logging import get_logger
from app.db.models import ActivityFeedORM, NotificationORM, SessionORM, SkateSpotORM
from app.models.activity import ActivityActor
from app.models.notification import (
    Notification,
    NotificationBulkUpdateResult,
    NotificationListResponse,
    NotificationType,
    NotificationUnreadCount,
)
from app.repositories.follow_repository import FollowRepository
from app.repositories.notification_repository import NotificationCreateData, NotificationRepository
from app.repositories.user_repository import UserRepository

if TYPE_CHECKING:  # pragma: no cover
    from sqlalchemy.orm import Session


class NotificationService:
    """Business logic for creating and retrieving notifications."""

    def __init__(self, db: Any) -> None:
        self.db: Session = db
        self._notifications = NotificationRepository(db)
        self._follows = FollowRepository(db)
        self._users = UserRepository(db)
        self._logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_notifications(
        self,
        user_id: str,
        *,
        include_read: bool,
        limit: int,
        offset: int,
    ) -> NotificationListResponse:
        """Return notifications for a user."""

        records, total = self._notifications.list_for_user(
            user_id,
            include_read=include_read,
            limit=limit,
            offset=offset,
        )
        unread_count = self._notifications.count_unread(user_id)
        notifications = [self._to_model(record) for record in records]
        has_more = (offset + len(notifications)) < total
        return NotificationListResponse(
            notifications=notifications,
            total=total,
            unread_count=unread_count,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )

    def unread_count(self, user_id: str) -> NotificationUnreadCount:
        """Return unread notification count."""

        return NotificationUnreadCount(unread_count=self._notifications.count_unread(user_id))

    def mark_as_read(self, notification_id: str, user_id: str) -> Notification | None:
        """Mark an individual notification as read."""

        record = self._notifications.mark_as_read(notification_id, user_id)
        if record is None:
            return None
        return self._to_model(record)

    def mark_all_as_read(self, user_id: str) -> NotificationBulkUpdateResult:
        """Mark all unread notifications as read."""

        updated = self._notifications.mark_all_as_read(user_id)
        unread_count = self._notifications.count_unread(user_id)
        return NotificationBulkUpdateResult(updated=updated, unread_count=unread_count)

    # ------------------------------------------------------------------
    # Creation helpers used by activity service
    # ------------------------------------------------------------------
    def notify_followers_of_activity(
        self,
        activity: ActivityFeedORM,
        *,
        metadata: dict | None = None,
        exclude_user_ids: set[str] | None = None,
    ) -> None:
        """Send a notification to followers of the acting user."""

        follower_ids = self._follows.list_follower_ids(activity.user_id)
        excluded = exclude_user_ids or set()
        payloads = [
            NotificationCreateData(
                user_id=follower_id,
                actor_id=activity.user_id,
                activity_id=activity.id,
                notification_type=activity.activity_type,
                metadata=self._augment_metadata(metadata, source="followers"),
            )
            for follower_id in follower_ids
            if follower_id not in excluded and follower_id != activity.user_id
        ]
        if not payloads:
            return

        try:
            self._notifications.bulk_create(payloads)
        except Exception as exc:  # pragma: no cover - defensive logging
            self._logger.warning("failed to create follower notifications", error=str(exc))

    def notify_spot_owner(
        self,
        spot_id: str,
        activity: ActivityFeedORM,
        *,
        metadata: dict | None = None,
        actor_id: str | None = None,
    ) -> str | None:
        """Notify the owner of the referenced spot."""

        spot = self.db.get(SkateSpotORM, spot_id)
        if spot is None:
            return None

        owner_id = spot.user_id
        if owner_id in {None, actor_id}:
            return owner_id

        payload = NotificationCreateData(
            user_id=owner_id,
            actor_id=actor_id,
            activity_id=activity.id,
            notification_type=activity.activity_type,
            metadata=self._augment_metadata(
                metadata,
                source="spot_owner",
                spot_id=spot_id,
                spot_name=spot.name,
            ),
        )
        try:
            self._notifications.create(payload)
        except Exception as exc:  # pragma: no cover - defensive logging
            self._logger.warning("failed to notify spot owner", error=str(exc))
        return owner_id

    def notify_session_organizer(
        self,
        session_id: str,
        activity: ActivityFeedORM,
        *,
        metadata: dict | None = None,
        actor_id: str | None = None,
    ) -> str | None:
        """Notify the organizer when someone interacts with their session."""

        session = self.db.get(SessionORM, session_id)
        if session is None:
            return None

        organizer_id = session.organizer_id
        if organizer_id in {None, actor_id}:
            return organizer_id

        payload = NotificationCreateData(
            user_id=organizer_id,
            actor_id=actor_id,
            activity_id=activity.id,
            notification_type=activity.activity_type,
            metadata=self._augment_metadata(
                metadata,
                source="session_host",
                session_id=session_id,
                session_title=session.title,
            ),
        )
        try:
            self._notifications.create(payload)
        except Exception as exc:  # pragma: no cover - defensive logging
            self._logger.warning("failed to notify session organizer", error=str(exc))
        return organizer_id

    def delete_for_activity(self, activity_id: str) -> None:
        """Cleanup notifications pointing at a removed activity."""

        self._notifications.delete_for_activity(activity_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _to_model(self, notification: NotificationORM) -> Notification:
        """Convert ORM notification into API model."""

        metadata = None
        if notification.notification_metadata:
            try:
                metadata = json.loads(notification.notification_metadata)
            except (TypeError, ValueError):  # pragma: no cover - defensive
                metadata = None

        actor_model = None
        if notification.actor:
            actor_model = ActivityActor(
                id=UUID(notification.actor.id),
                username=notification.actor.username,
                display_name=notification.actor.display_name,
                profile_photo_url=notification.actor.profile_photo_url,
            )

        message = self._build_message(notification.notification_type, actor_model, metadata)

        return Notification(
            id=UUID(notification.id),
            notification_type=NotificationType(notification.notification_type),
            activity_id=UUID(notification.activity_id) if notification.activity_id else None,
            message=message,
            metadata=metadata,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
            actor=actor_model,
        )

    @staticmethod
    def _augment_metadata(
        base: dict | None,
        **extra: str | int | None,
    ) -> dict | None:
        metadata: dict[str, str | int] = {}
        if base:
            metadata.update(base)
        for key, value in extra.items():
            if value is not None:
                metadata[key] = value
        return metadata or None

    @staticmethod
    def _actor_name(actor: ActivityActor | None) -> str:
        if actor is None:
            return "Someone"
        return actor.display_name or actor.username

    def _build_message(
        self,
        notification_type: str,
        actor: ActivityActor | None,
        metadata: dict | None,
    ) -> str | None:
        """Generate a short human-readable message."""

        try:
            notification_enum = NotificationType(notification_type)
        except ValueError:  # pragma: no cover - defensive
            return None

        name = self._actor_name(actor)
        source = (metadata or {}).get("source")

        if notification_enum is NotificationType.SPOT_CREATED:
            spot_name = (metadata or {}).get("spot_name")
            if spot_name:
                return f'{name} added a new spot "{spot_name}"'
            return f"{name} added a new spot"

        if notification_enum is NotificationType.SPOT_COMMENTED:
            spot_name = (metadata or {}).get("spot_name")
            if source == "spot_owner":
                if spot_name:
                    return f'{name} commented on your spot "{spot_name}"'
                return f"{name} commented on your spot"
            if spot_name:
                return f'{name} commented on "{spot_name}"'
            return f"{name} left a comment"

        if notification_enum is NotificationType.SPOT_RATED:
            spot_name = (metadata or {}).get("spot_name")
            score = (metadata or {}).get("score")
            if source == "spot_owner":
                if spot_name and score:
                    return f'{name} rated your spot "{spot_name}" {score}/5'
                if spot_name:
                    return f'{name} rated your spot "{spot_name}"'
                if score:
                    return f"{name} rated your spot {score}/5"
                return f"{name} rated your spot"
            if spot_name and score:
                return f'{name} rated "{spot_name}" {score}/5'
            if spot_name:
                return f'{name} rated "{spot_name}"'
            return f"{name} left a rating"

        if notification_enum is NotificationType.SPOT_FAVORITED:
            spot_name = (metadata or {}).get("spot_name")
            if source == "spot_owner":
                if spot_name:
                    return f'{name} favorited your spot "{spot_name}"'
                return f"{name} favorited your spot"
            if spot_name:
                return f'{name} favorited "{spot_name}"'
            return f"{name} favorited a spot"

        if notification_enum is NotificationType.SESSION_CREATED:
            session_title = (metadata or {}).get("session_title")
            if session_title:
                return f'{name} scheduled a session "{session_title}"'
            return f"{name} scheduled a session"

        if notification_enum is NotificationType.SESSION_RSVP:
            session_title = (metadata or {}).get("session_title")
            response = (metadata or {}).get("response")
            if session_title and response:
                return f'{name} responded "{response}" to your session "{session_title}"'
            if session_title:
                return f'{name} responded to your session "{session_title}"'
            return f"{name} updated an RSVP"

        return None


def get_notification_service(
    db: Annotated[Any, Depends(get_db)],
) -> NotificationService:
    """Dependency provider for notification service."""

    return NotificationService(db)
