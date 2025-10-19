"""Tests for the comment service layer."""

from uuid import uuid4

import pytest

from app.core.security import get_password_hash
from app.models.comment import CommentCreate
from app.models.skate_spot import Difficulty, Location, SkateSpotCreate, SpotType
from app.models.user import UserCreate
from app.repositories.comment_repository import CommentRepository
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.repositories.user_repository import UserRepository
from app.services.comment_service import (
    CommentNotFoundError,
    CommentPermissionError,
    CommentService,
    SpotNotFoundError,
)


@pytest.fixture
def spot_repository(session_factory):
    return SkateSpotRepository(session_factory=session_factory)


@pytest.fixture
def comment_service(session_factory, spot_repository):
    comment_repository = CommentRepository(session_factory=session_factory)
    return CommentService(comment_repository, spot_repository)


@pytest.fixture
def sample_spot(spot_repository, test_user):
    payload = SkateSpotCreate(
        name="Service Comment Spot",
        description="Spot for testing comment service",
        spot_type=SpotType.PARK,
        difficulty=Difficulty.INTERMEDIATE,
        location=Location(
            latitude=34.0522,
            longitude=-118.2437,
            city="Los Angeles",
            country="USA",
        ),
        is_public=True,
        requires_permission=False,
    )
    return spot_repository.create(payload, user_id=test_user.id)


@pytest.fixture
def other_user(session_factory):
    db = session_factory()
    try:
        repo = UserRepository(db)
        user_data = UserCreate(
            email="other@example.com",
            username="otheruser",
            password="password456",
        )
        hashed = get_password_hash("password456")
        user = repo.create(user_data, hashed)
        db.expunge(user)
        return user
    finally:
        db.close()


def test_add_comment_returns_updated_list(comment_service, sample_spot, test_user):
    """Adding a comment returns the refreshed comment list."""

    comments = comment_service.add_comment(
        sample_spot.id,
        test_user,
        CommentCreate(content="Plenty of shade here."),
    )

    assert len(comments) == 1
    assert comments[0].content == "Plenty of shade here."


def test_delete_comment_as_owner(comment_service, sample_spot, test_user):
    """The comment author can delete their own comment."""

    comments = comment_service.add_comment(
        sample_spot.id,
        test_user,
        CommentCreate(content="I'll delete this"),
    )
    comment_id = comments[0].id

    remaining = comment_service.delete_comment(sample_spot.id, comment_id, test_user)
    assert remaining == []


def test_delete_comment_as_admin(comment_service, sample_spot, test_user, test_admin):
    """Admins can remove comments created by other users."""

    comments = comment_service.add_comment(
        sample_spot.id,
        test_user,
        CommentCreate(content="Admin cleanup"),
    )
    comment_id = comments[0].id

    remaining = comment_service.delete_comment(sample_spot.id, comment_id, test_admin)
    assert remaining == []


def test_delete_comment_without_permission(comment_service, sample_spot, test_user, other_user):
    """Non-owners who are not admins cannot delete other users' comments."""

    comments = comment_service.add_comment(
        sample_spot.id,
        test_user,
        CommentCreate(content="Can't touch this"),
    )
    comment_id = comments[0].id

    with pytest.raises(CommentPermissionError):
        comment_service.delete_comment(sample_spot.id, comment_id, other_user)


def test_delete_missing_comment_raises(comment_service, sample_spot, test_user):
    """Deleting a missing comment raises an error."""

    with pytest.raises(CommentNotFoundError):
        comment_service.delete_comment(sample_spot.id, uuid4(), test_user)


def test_comment_spot_not_found(comment_service, test_user):
    """Actions against a missing spot raise SpotNotFoundError."""

    missing_spot = uuid4()
    with pytest.raises(SpotNotFoundError):
        comment_service.add_comment(missing_spot, test_user, CommentCreate(content="Test"))

    with pytest.raises(SpotNotFoundError):
        comment_service.list_comments(missing_spot)

    with pytest.raises(SpotNotFoundError):
        comment_service.delete_comment(missing_spot, uuid4(), test_user)
