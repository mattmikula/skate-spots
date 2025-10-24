"""Business logic for skate spot comments."""

from __future__ import annotations

import uuid  # noqa: TC003
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends

from app.core.dependencies import get_db
from app.core.logging import get_logger
from app.models.comment import Comment, CommentCreate  # noqa: TC001
from app.repositories.comment_repository import CommentRepository
from app.repositories.skate_spot_repository import SkateSpotRepository

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from app.db.models import UserORM
    from app.models.skate_spot import SkateSpot
    from app.services.activity_service import ActivityService


class SpotNotFoundError(Exception):
    """Raised when the associated skate spot does not exist."""


class CommentNotFoundError(Exception):
    """Raised when a comment cannot be located."""


class CommentPermissionError(Exception):
    """Raised when a user attempts to modify a comment they do not own."""


class CommentService:
    """Coordinate comment persistence and domain rules."""

    def __init__(
        self,
        comment_repository: CommentRepository,
        skate_spot_repository: SkateSpotRepository,
        activity_service: ActivityService | None = None,
    ) -> None:
        self._comment_repository = comment_repository
        self._skate_spot_repository = skate_spot_repository
        self._activity_service = activity_service
        self._logger = get_logger(__name__)

    def _ensure_spot_exists(self, spot_id: uuid.UUID) -> SkateSpot:
        spot = self._skate_spot_repository.get_by_id(spot_id)
        if spot is None:
            self._logger.warning("comment requested for missing spot", spot_id=str(spot_id))
            raise SpotNotFoundError(f"Skate spot with id {spot_id} not found.")
        return spot

    def list_comments(self, spot_id: uuid.UUID) -> list[Comment]:
        """Return all comments for a skate spot."""

        self._ensure_spot_exists(spot_id)
        return self._comment_repository.list_for_spot(spot_id)

    def add_comment(self, spot_id: uuid.UUID, user: UserORM, data: CommentCreate) -> list[Comment]:
        """Add a new comment to the skate spot and return the refreshed list."""

        self._ensure_spot_exists(spot_id)
        comment = self._comment_repository.create(spot_id, user.id, data)
        self._logger.info(
            "comment created",
            spot_id=str(spot_id),
            user_id=user.id,
            comment_id=str(comment.id),
        )

        # Record activity
        if self._activity_service:
            try:
                self._activity_service.record_spot_commented(
                    str(user.id), str(spot_id), str(comment.id)
                )
            except Exception as e:
                self._logger.warning("failed to record comment activity", error=str(e))

        return self._comment_repository.list_for_spot(spot_id)

    def delete_comment(
        self, spot_id: uuid.UUID, comment_id: uuid.UUID, user: UserORM
    ) -> list[Comment]:
        """Delete a comment owned by the user or by any user if admin."""

        self._ensure_spot_exists(spot_id)
        comment = self._comment_repository.get_by_id(comment_id)
        if comment is None or comment.spot_id != spot_id:
            self._logger.debug(
                "delete requested for missing comment",
                spot_id=str(spot_id),
                comment_id=str(comment_id),
            )
            raise CommentNotFoundError("Comment not found for this skate spot.")

        is_owner = str(comment.user_id) == str(user.id)
        if not (is_owner or user.is_admin):
            self._logger.debug(
                "comment delete forbidden",
                spot_id=str(spot_id),
                comment_id=str(comment_id),
                user_id=user.id,
            )
            raise CommentPermissionError("You do not have permission to delete this comment.")

        deleted = self._comment_repository.delete(comment_id)
        if not deleted:
            raise CommentNotFoundError("Comment not found for this skate spot.")

        self._logger.info(
            "comment deleted",
            spot_id=str(spot_id),
            comment_id=str(comment_id),
            user_id=user.id,
        )
        return self._comment_repository.list_for_spot(spot_id)


def get_comment_service(
    db: Annotated[Any, Depends(get_db)],
) -> CommentService:
    """FastAPI dependency hook to create comment service with activity tracking.

    Args:
        db: Database session from dependency injection

    Returns:
        CommentService instance with repositories initialized
    """
    from app.services.activity_service import get_activity_service

    comment_repository = CommentRepository()
    skate_spot_repository = SkateSpotRepository()
    activity_service = get_activity_service(db)
    return CommentService(comment_repository, skate_spot_repository, activity_service)
