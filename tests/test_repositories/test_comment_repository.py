"""Tests for the comment repository."""

from uuid import UUID

import pytest

from app.models.comment import CommentCreate
from app.models.skate_spot import Difficulty, Location, SkateSpotCreate, SpotType
from app.repositories.comment_repository import CommentRepository
from app.repositories.skate_spot_repository import SkateSpotRepository


@pytest.fixture
def comment_repository(session_factory):
    """Comment repository bound to the in-memory database."""

    return CommentRepository(session_factory=session_factory)


@pytest.fixture
def spot_repository(session_factory):
    """Skate spot repository for creating fixtures."""

    return SkateSpotRepository(session_factory=session_factory)


@pytest.fixture
def sample_spot(spot_repository, test_user):
    """Create a sample skate spot owned by the test user."""

    data = SkateSpotCreate(
        name="Comment Test Spot",
        description="Spot used for testing comments",
        spot_type=SpotType.STREET,
        difficulty=Difficulty.BEGINNER,
        location=Location(
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
        ),
        is_public=True,
        requires_permission=False,
    )
    return spot_repository.create(data, user_id=test_user.id)


def test_create_comment(comment_repository, sample_spot, test_user):
    """Creating a comment persists it and returns the Pydantic model."""

    comment = comment_repository.create(
        sample_spot.id,
        user_id=test_user.id,
        payload=CommentCreate(content="Love the manual pads here!"),
    )

    assert comment.content == "Love the manual pads here!"
    assert comment.author.username == test_user.username
    assert isinstance(comment.user_id, UUID)


def test_list_comments_orders_by_most_recent(comment_repository, sample_spot, test_user):
    """Listing comments returns the newest entries first."""

    first = comment_repository.create(
        sample_spot.id,
        user_id=test_user.id,
        payload=CommentCreate(content="First!"),
    )
    second = comment_repository.create(
        sample_spot.id,
        user_id=test_user.id,
        payload=CommentCreate(content="Second comment"),
    )

    comments = comment_repository.list_for_spot(sample_spot.id)
    assert comments[0].id == second.id
    assert comments[1].id == first.id


def test_get_by_id_returns_comment(comment_repository, sample_spot, test_user):
    """Comments can be retrieved by identifier."""

    created = comment_repository.create(
        sample_spot.id,
        user_id=test_user.id,
        payload=CommentCreate(content="Checking retrieval"),
    )

    fetched = comment_repository.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.content == "Checking retrieval"


def test_delete_comment(comment_repository, sample_spot, test_user):
    """Deleting a comment returns True and removes it."""

    comment = comment_repository.create(
        sample_spot.id,
        user_id=test_user.id,
        payload=CommentCreate(content="Remove me"),
    )

    assert comment_repository.delete(comment.id) is True
    assert comment_repository.get_by_id(comment.id) is None


def test_delete_missing_comment_returns_false(comment_repository):
    """Attempting to delete a non-existent comment returns False."""

    random_id = UUID("00000000-0000-0000-0000-000000000001")
    assert comment_repository.delete(random_id) is False
