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
        """Send a notification to followers of the acting user.

        This method uses batched processing to efficiently handle users with
        large numbers of followers without loading all follower IDs into memory
        at once.
        """
        excluded = exclude_user_ids or set()

        # Process followers in batches for memory efficiency
        batches = self._follows.iter_follower_ids_batched(activity.user_id, batch_size=100)

        for follower_batch in batches:
            payloads = [
                NotificationCreateData(
                    user_id=follower_id,
                    actor_id=activity.user_id,
                    activity_id=activity.id,
                    notification_type=activity.activity_type,
                    metadata=self._augment_metadata(metadata, source="followers"),
                )
                for follower_id in follower_batch
                if follower_id not in excluded and follower_id != activity.user_id
            ]

            if not payloads:
                continue

            try:
                self._notifications.bulk_create(payloads)
            except Exception as exc:  # pragma: no cover - defensive logging
                self._logger.warning(
                    "failed to create follower notifications for batch", error=str(exc)
                )

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
    ) -> str:
        """Generate a short human-readable message.

        This method always returns a valid message string. If the notification
        type is unrecognized, it returns a generic message.
        """
        metadata = metadata or {}
        try:
            notification_enum = NotificationType(notification_type)
        except ValueError:  # pragma: no cover - defensive
            return "New activity"

        name = self._actor_name(actor)
        source = metadata.get("source")
        handler = {
            NotificationType.SPOT_CREATED: self._spot_created_message,
            NotificationType.SPOT_COMMENTED: self._spot_commented_message,
            NotificationType.SPOT_RATED: self._spot_rated_message,
            NotificationType.SPOT_FAVORITED: self._spot_favorited_message,
            NotificationType.SPOT_CHECKED_IN: self._spot_checked_in_message,
            NotificationType.SESSION_CREATED: self._session_created_message,
            NotificationType.SESSION_RSVP: self._session_rsvp_message,
        }.get(notification_enum)

        if handler is None:
            return f"{name} has new activity"
        return handler(name, metadata, source)

    def _spot_created_message(self, name: str, metadata: dict, _source: str | None) -> str:
        spot_name = metadata.get("spot_name")
        return self._select_message(
            (bool(spot_name), f'{name} added a new spot "{spot_name}"'),
            (True, f"{name} added a new spot"),
        )

    def _spot_commented_message(self, name: str, metadata: dict, source: str | None) -> str:
        spot_name = metadata.get("spot_name")
        return self._select_message(
            (
                source == "spot_owner" and bool(spot_name),
                f'{name} commented on your spot "{spot_name}"',
            ),
            (source == "spot_owner", f"{name} commented on your spot"),
            (bool(spot_name), f'{name} commented on "{spot_name}"'),
            (True, f"{name} left a comment"),
        )

    def _spot_rated_message(self, name: str, metadata: dict, source: str | None) -> str:
        spot_name = metadata.get("spot_name")
        score = metadata.get("score")
        has_spot_name = bool(spot_name)
        has_score = score is not None
        return self._select_message(
            (
                source == "spot_owner" and has_spot_name and has_score,
                f'{name} rated your spot "{spot_name}" {score}/5',
            ),
            (source == "spot_owner" and has_spot_name, f'{name} rated your spot "{spot_name}"'),
            (source == "spot_owner" and has_score, f"{name} rated your spot {score}/5"),
            (source == "spot_owner", f"{name} rated your spot"),
            (has_spot_name and has_score, f'{name} rated "{spot_name}" {score}/5'),
            (has_spot_name, f'{name} rated "{spot_name}"'),
            (True, f"{name} left a rating"),
        )

    def _spot_favorited_message(self, name: str, metadata: dict, source: str | None) -> str:
        spot_name = metadata.get("spot_name")
        return self._select_message(
            (
                source == "spot_owner" and bool(spot_name),
                f'{name} favorited your spot "{spot_name}"',
            ),
            (source == "spot_owner", f"{name} favorited your spot"),
            (bool(spot_name), f'{name} favorited "{spot_name}"'),
            (True, f"{name} favorited a spot"),
        )

    def _spot_checked_in_message(self, name: str, metadata: dict, source: str | None) -> str:
        spot_name = metadata.get("spot_name")
        heading = metadata.get("status") == "heading"
        return self._select_message(
            (
                source == "spot_owner" and heading and bool(spot_name),
                f'{name} is heading to your spot "{spot_name}"',
            ),
            (source == "spot_owner" and bool(spot_name), f'{name} is at your spot "{spot_name}"'),
            (source == "spot_owner" and heading, f"{name} is heading to your spot"),
            (source == "spot_owner", f"{name} is at your spot"),
            (heading and bool(spot_name), f'{name} is heading to "{spot_name}"'),
            (bool(spot_name), f'{name} checked in at "{spot_name}"'),
            (heading, f"{name} is heading to a spot"),
            (True, f"{name} checked in at a spot"),
        )

    def _session_created_message(self, name: str, metadata: dict, _source: str | None) -> str:
        session_title = metadata.get("session_title")
        return self._select_message(
            (bool(session_title), f'{name} scheduled a session "{session_title}"'),
            (True, f"{name} scheduled a session"),
        )

    def _session_rsvp_message(self, name: str, metadata: dict, _source: str | None) -> str:
        session_title = metadata.get("session_title")
        response = metadata.get("response")
        has_session_title = session_title is not None
        has_response = response is not None
        return self._select_message(
            (
                has_session_title and has_response,
                f'{name} responded "{response}" to your session "{session_title}"',
            ),
            (has_session_title, f'{name} responded to your session "{session_title}"'),
            (True, f"{name} updated an RSVP"),
        )

    @staticmethod
    def _select_message(*candidates: tuple[bool, str]) -> str:
        """Return the first candidate whose condition is truthy.

        The final candidate is expected to be an unconditional fallback (condition is True).
        Raises ValueError if no candidates are provided or the fallback is missing.
        """
        if not candidates:
            raise ValueError("_select_message requires at least one candidate")
        for condition, message in candidates:
            if condition:
                return message
        raise ValueError("_select_message requires at least one candidate with a true condition")


def get_notification_service(
    db: Annotated[Any, Depends(get_db)],
) -> NotificationService:
    """Dependency provider for notification service."""

    return NotificationService(db)
