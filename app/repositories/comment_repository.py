"""Repository layer for skate spot comments."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.database import SessionLocal
from app.db.models import SpotCommentORM
from app.models.comment import Comment, CommentAuthor, CommentCreate

SessionFactory = Callable[[], Session]


def _orm_to_pydantic(comment: SpotCommentORM) -> Comment:
    """Convert an ORM comment instance into its Pydantic representation."""

    if comment.author is not None:
        author = CommentAuthor(id=UUID(comment.author.id), username=comment.author.username)
    else:
        author = CommentAuthor(id=UUID(comment.user_id), username="Unknown skater")

    return Comment(
        id=UUID(comment.id),
        spot_id=UUID(comment.spot_id),
        user_id=UUID(comment.user_id),
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author=author,
    )


class CommentRepository:
    """Persistence helpers for skate spot comments."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or SessionLocal

    def create(self, spot_id: UUID, user_id: str, payload: CommentCreate) -> Comment:
        """Persist a new comment for the given spot and user."""

        with self._session_factory() as session:
            comment = SpotCommentORM(
                spot_id=str(spot_id),
                user_id=str(user_id),
                content=payload.content,
            )
            session.add(comment)
            session.commit()
            session.refresh(comment)
            _ = comment.author  # eager load for conversion
            return _orm_to_pydantic(comment)

    def list_for_spot(self, spot_id: UUID) -> list[Comment]:
        """Return all comments associated with a skate spot ordered by recency."""

        with self._session_factory() as session:
            stmt = (
                select(SpotCommentORM)
                .options(selectinload(SpotCommentORM.author))
                .where(SpotCommentORM.spot_id == str(spot_id))
                .order_by(SpotCommentORM.created_at.desc())
            )
            comments = session.scalars(stmt).all()
            return [_orm_to_pydantic(comment) for comment in comments]

    def get_by_id(self, comment_id: UUID) -> Comment | None:
        """Return a comment by its identifier if it exists."""

        with self._session_factory() as session:
            stmt = (
                select(SpotCommentORM)
                .options(selectinload(SpotCommentORM.author))
                .where(SpotCommentORM.id == str(comment_id))
            )
            comment = session.scalars(stmt).one_or_none()
            return _orm_to_pydantic(comment) if comment else None

    def delete(self, comment_id: UUID) -> bool:
        """Delete a comment by identifier, returning ``True`` if one was removed."""

        with self._session_factory() as session:
            stmt = select(SpotCommentORM).where(SpotCommentORM.id == str(comment_id))
            comment = session.scalars(stmt).one_or_none()
            if comment is None:
                return False

            session.delete(comment)
            session.commit()
            return True
