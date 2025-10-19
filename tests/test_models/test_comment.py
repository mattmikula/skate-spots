"""Unit tests for the comment Pydantic models."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.models.comment import Comment, CommentAuthor, CommentCreate


def test_comment_create_strips_whitespace():
    """Leading and trailing whitespace is removed from comment content."""

    payload = CommentCreate(content="   Great spot!   ")
    assert payload.content == "Great spot!"


def test_comment_create_rejects_blank():
    """Blank comments raise validation errors."""

    with pytest.raises(ValidationError):
        CommentCreate(content="   ")


def test_comment_model_round_trip():
    """Persisted comment data can be loaded into the Comment model."""

    comment_id = uuid4()
    spot_id = uuid4()
    user_id = uuid4()
    timestamp = datetime.now(UTC)

    comment = Comment(
        id=comment_id,
        spot_id=spot_id,
        user_id=user_id,
        content="Loved the ledges here!",
        created_at=timestamp,
        updated_at=timestamp,
        author=CommentAuthor(id=user_id, username="skater"),
    )

    assert comment.id == comment_id
    assert isinstance(comment.user_id, UUID)
    assert comment.author.username == "skater"
    assert comment.content == "Loved the ledges here!"
