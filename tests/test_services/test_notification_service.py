"""Tests for the notification service."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.db.models import UserORM
from app.models.notification import NotificationType
from app.repositories.notification_repository import NotificationCreateData, NotificationRepository
from app.services.notification_service import NotificationService


@pytest.fixture
def notification_service(db):
    """Provide notification service with test session."""
    return NotificationService(db)


@pytest.fixture
def test_users(db):
    """Create users to act as recipient and actor."""
    recipient = UserORM(
        email="recipient@example.com",
        username="recipient",
        hashed_password="secret",
    )
    actor = UserORM(
        email="actor@example.com",
        username="actor",
        hashed_password="secret",
    )
    db.add_all([recipient, actor])
    db.commit()
    return recipient, actor


class TestNotificationService:
    """Behavioural tests for NotificationService."""

    def test_list_and_mark_notifications(
        self,
        notification_service: NotificationService,
        db,
        test_users,
    ):
        """Notifications should list in reverse chronological order and support marking read."""
        recipient, actor = test_users
        repo = NotificationRepository(db)

        first = repo.create(
            NotificationCreateData(
                user_id=recipient.id,
                actor_id=actor.id,
                activity_id=str(uuid4()),
                notification_type=NotificationType.SPOT_CREATED.value,
                metadata={"spot_name": "Courthouse Ledge"},
            )
        )
        second = repo.create(
            NotificationCreateData(
                user_id=recipient.id,
                actor_id=actor.id,
                activity_id=str(uuid4()),
                notification_type=NotificationType.SPOT_COMMENTED.value,
                metadata={"spot_name": "Courthouse Ledge", "source": "spot_owner"},
            )
        )

        response = notification_service.list_notifications(
            recipient.id,
            include_read=True,
            limit=10,
            offset=0,
        )

        assert response.total == 2
        assert response.unread_count == 2
        assert [str(notif.id) for notif in response.notifications] == [second.id, first.id]

        marked = notification_service.mark_as_read(str(second.id), recipient.id)
        assert marked is not None
        assert marked.is_read is True
        assert notification_service.unread_count(recipient.id).unread_count == 1

        bulk = notification_service.mark_all_as_read(recipient.id)
        assert bulk.updated >= 1
        assert bulk.unread_count == 0

        missing = notification_service.mark_as_read(str(uuid4()), recipient.id)
        assert missing is None
