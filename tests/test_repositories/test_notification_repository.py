"""Tests for the notification repository."""

from uuid import UUID

import pytest

from app.repositories.notification_repository import (
    NotificationCreateData,
    NotificationRepository,
)


@pytest.fixture
def notification_repository(session_factory):
    """Notification repository bound to the in-memory database."""
    db = session_factory()
    try:
        yield NotificationRepository(db)
    finally:
        db.close()


@pytest.fixture
def second_user(session_factory):
    """Create a second test user for actor/recipient scenarios."""
    from app.core.security import get_password_hash
    from app.models.user import UserCreate
    from app.repositories.user_repository import UserRepository

    db = session_factory()
    try:
        repo = UserRepository(db)
        user_data = UserCreate(
            email="seconduser@example.com",
            username="seconduser",
            password="password123",
        )
        hashed_password = get_password_hash("password123")
        user = repo.create(user_data, hashed_password)
        db.expunge(user)
        return user
    finally:
        db.close()


def test_create_notification(notification_repository, test_user, second_user):
    """Creating a notification persists it and returns the ORM model."""
    payload = NotificationCreateData(
        user_id=test_user.id,
        notification_type="spot_commented",
        actor_id=second_user.id,
        metadata={"spot_name": "Test Skate Park"},
    )

    notification = notification_repository.create(payload)

    assert notification.user_id == test_user.id
    assert notification.actor_id == second_user.id
    assert notification.notification_type == "spot_commented"
    assert notification.is_read is False
    assert notification.read_at is None
    assert notification.notification_metadata is not None


def test_create_notification_without_metadata(notification_repository, test_user):
    """Notifications can be created without metadata."""
    payload = NotificationCreateData(
        user_id=test_user.id,
        notification_type="spot_created",
    )

    notification = notification_repository.create(payload)

    assert notification.notification_metadata is None


def test_bulk_create_notifications(notification_repository, test_user, second_user):
    """Bulk creating notifications creates all in one transaction."""
    payloads = [
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_rated",
            actor_id=second_user.id,
        ),
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_commented",
            actor_id=second_user.id,
        ),
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="session_created",
            actor_id=second_user.id,
        ),
    ]

    notifications = notification_repository.bulk_create(payloads)

    assert len(notifications) == 3
    assert all(n.user_id == test_user.id for n in notifications)
    assert notifications[0].notification_type == "spot_rated"
    assert notifications[1].notification_type == "spot_commented"
    assert notifications[2].notification_type == "session_created"


def test_bulk_create_empty_list_returns_empty(notification_repository):
    """Bulk creating an empty list returns an empty list."""
    notifications = notification_repository.bulk_create([])
    assert notifications == []


def test_list_for_user_unread_only(notification_repository, test_user, second_user):
    """Listing notifications can filter to unread only."""
    # Create mix of read and unread
    n1 = notification_repository.create(
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_commented",
        )
    )
    n2 = notification_repository.create(
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_rated",
        )
    )
    notification_repository.create(
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_favorited",
        )
    )

    # Mark one as read
    notification_repository.mark_as_read(n1.id, test_user.id)

    # List unread only
    notifications, total = notification_repository.list_for_user(
        test_user.id,
        include_read=False,
        limit=10,
        offset=0,
    )

    assert len(notifications) == 2
    assert total == 2
    assert all(n.id != n1.id for n in notifications)


def test_list_for_user_include_read(notification_repository, test_user):
    """Listing notifications can include read notifications."""
    n1 = notification_repository.create(
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_commented",
        )
    )
    notification_repository.create(
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_rated",
        )
    )

    notification_repository.mark_as_read(n1.id, test_user.id)

    notifications, total = notification_repository.list_for_user(
        test_user.id,
        include_read=True,
        limit=10,
        offset=0,
    )

    assert len(notifications) == 2
    assert total == 2


def test_list_for_user_pagination(notification_repository, test_user):
    """Listing notifications supports pagination."""
    # Create 5 notifications
    types = ["spot_created", "spot_rated", "spot_commented", "spot_favorited", "session_created"]
    for notification_type in types:
        notification_repository.create(
            NotificationCreateData(
                user_id=test_user.id,
                notification_type=notification_type,
            )
        )

    # Get first page
    page1, total = notification_repository.list_for_user(
        test_user.id,
        include_read=False,
        limit=2,
        offset=0,
    )

    # Get second page
    page2, _ = notification_repository.list_for_user(
        test_user.id,
        include_read=False,
        limit=2,
        offset=2,
    )

    assert len(page1) == 2
    assert len(page2) == 2
    assert total == 5
    assert page1[0].id != page2[0].id


def test_list_for_user_ordered_by_recency(notification_repository, test_user):
    """Notifications are ordered newest first."""
    n1 = notification_repository.create(
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_created",
        )
    )
    n2 = notification_repository.create(
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_rated",
        )
    )
    n3 = notification_repository.create(
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_commented",
        )
    )

    notifications, _ = notification_repository.list_for_user(
        test_user.id,
        include_read=False,
        limit=10,
        offset=0,
    )

    assert notifications[0].id == n3.id  # Most recent first
    assert notifications[1].id == n2.id
    assert notifications[2].id == n1.id


def test_mark_as_read_updates_notification(notification_repository, test_user):
    """Marking a notification as read sets the flag and timestamp."""
    notification = notification_repository.create(
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_commented",
        )
    )

    updated = notification_repository.mark_as_read(notification.id, test_user.id)

    assert updated is not None
    assert updated.is_read is True
    assert updated.read_at is not None


def test_mark_as_read_already_read_is_idempotent(notification_repository, test_user):
    """Marking an already-read notification does nothing but returns it."""
    notification = notification_repository.create(
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_commented",
        )
    )

    # Mark once
    first_update = notification_repository.mark_as_read(notification.id, test_user.id)
    first_read_at = first_update.read_at

    # Mark again
    second_update = notification_repository.mark_as_read(notification.id, test_user.id)

    assert second_update.read_at == first_read_at
    assert second_update.is_read is True


def test_mark_as_read_wrong_user_returns_none(notification_repository, test_user, second_user):
    """Attempting to mark another user's notification returns None."""
    notification = notification_repository.create(
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_commented",
        )
    )

    result = notification_repository.mark_as_read(notification.id, second_user.id)

    assert result is None


def test_mark_as_read_nonexistent_returns_none(notification_repository, test_user):
    """Attempting to mark a non-existent notification returns None."""
    fake_id = "00000000-0000-0000-0000-000000000001"
    result = notification_repository.mark_as_read(fake_id, test_user.id)
    assert result is None


def test_mark_all_as_read(notification_repository, test_user, second_user):
    """Marking all as read updates only the user's unread notifications."""
    # Create notifications for test_user
    notification_repository.create(
        NotificationCreateData(user_id=test_user.id, notification_type="spot_created")
    )
    notification_repository.create(
        NotificationCreateData(user_id=test_user.id, notification_type="spot_rated")
    )
    notification_repository.create(
        NotificationCreateData(user_id=test_user.id, notification_type="spot_commented")
    )

    # Create one for second_user
    notification_repository.create(
        NotificationCreateData(user_id=second_user.id, notification_type="spot_favorited")
    )

    count = notification_repository.mark_all_as_read(test_user.id)

    assert count == 3

    # Verify test_user has no unread
    unread_count = notification_repository.count_unread(test_user.id)
    assert unread_count == 0

    # Verify second_user still has 1 unread
    second_unread = notification_repository.count_unread(second_user.id)
    assert second_unread == 1


def test_count_unread(notification_repository, test_user):
    """Counting unread notifications returns the correct number."""
    # Create 3 notifications
    n1 = notification_repository.create(
        NotificationCreateData(user_id=test_user.id, notification_type="spot_created")
    )
    notification_repository.create(
        NotificationCreateData(user_id=test_user.id, notification_type="spot_rated")
    )
    notification_repository.create(
        NotificationCreateData(user_id=test_user.id, notification_type="spot_commented")
    )

    # Initially all unread
    assert notification_repository.count_unread(test_user.id) == 3

    # Mark one as read
    notification_repository.mark_as_read(n1.id, test_user.id)

    # Should now be 2
    assert notification_repository.count_unread(test_user.id) == 2


def test_count_unread_no_notifications(notification_repository, test_user):
    """Counting unread when user has none returns zero."""
    assert notification_repository.count_unread(test_user.id) == 0


def test_delete_for_activity(notification_repository, test_user, second_user):
    """Deleting notifications by activity ID removes them."""
    activity_id = "activity-123"

    # Create notifications tied to activity
    notification_repository.create(
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_commented",
            activity_id=activity_id,
        )
    )
    notification_repository.create(
        NotificationCreateData(
            user_id=second_user.id,
            notification_type="spot_rated",
            activity_id=activity_id,
        )
    )

    # Create one without activity_id
    notification_repository.create(
        NotificationCreateData(
            user_id=test_user.id,
            notification_type="spot_favorited",
        )
    )

    count = notification_repository.delete_for_activity(activity_id)

    assert count == 2

    # Verify only the one without activity_id remains
    remaining, total = notification_repository.list_for_user(
        test_user.id,
        include_read=False,
        limit=10,
        offset=0,
    )
    assert total == 1
    assert remaining[0].notification_type == "spot_favorited"


def test_delete_for_activity_nonexistent_returns_zero(notification_repository):
    """Deleting for a non-existent activity returns 0."""
    count = notification_repository.delete_for_activity("nonexistent-activity")
    assert count == 0
