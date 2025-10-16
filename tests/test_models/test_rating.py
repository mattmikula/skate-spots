"""Tests for rating models."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.models.rating import Rating, RatingCreate, RatingUpdate


def test_rating_create_valid():
    """RatingCreate accepts valid scores and optional comment."""

    rating = RatingCreate(score=5, comment="Great spot")
    assert rating.score == 5
    assert rating.comment == "Great spot"


def test_rating_create_score_out_of_range():
    """RatingCreate enforces score boundaries."""

    with pytest.raises(ValidationError):
        RatingCreate(score=0)

    with pytest.raises(ValidationError):
        RatingCreate(score=6)


def test_rating_update_allows_partial_fields():
    """RatingUpdate permits partial updates."""

    rating_update = RatingUpdate(comment="Updated comment")
    assert rating_update.comment == "Updated comment"
    assert rating_update.score is None


def test_rating_model_round_trip():
    """Rating model validates persisted data."""

    rating_id = uuid4()
    user_id = uuid4()
    spot_id = uuid4()
    timestamp = datetime.utcnow()

    rating = Rating(
        id=rating_id,
        user_id=user_id,
        spot_id=spot_id,
        score=3,
        comment=None,
        created_at=timestamp,
        updated_at=timestamp,
    )

    assert rating.id == rating_id
    assert isinstance(rating.user_id, UUID)
    assert rating.score == 3
