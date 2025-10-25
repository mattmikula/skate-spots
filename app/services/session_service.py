"""Business logic for skate session scheduling."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TCH003

from app.core.logging import get_logger
from app.models.session import (
    Session,
    SessionCreate,
    SessionResponse,
    SessionRSVPCreate,
    SessionStatus,
    SessionUpdate,
)
from app.repositories.session_repository import SessionRepository
from app.repositories.skate_spot_repository import SkateSpotRepository

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from app.db.models import UserORM
    from app.services.activity_service import ActivityService


class SessionSpotNotFoundError(Exception):
    """Raised when a target skate spot cannot be located."""


class SessionNotFoundError(Exception):
    """Raised when a session is missing."""


class SessionPermissionError(Exception):
    """Raised when a user attempts an action they are not permitted to perform."""


class SessionCapacityError(Exception):
    """Raised when an RSVP exceeds the available capacity."""


class SessionInactiveError(Exception):
    """Raised when interacting with cancelled or completed sessions."""


class SessionRSVPNotFoundError(Exception):
    """Raised when a user tries to withdraw an RSVP that does not exist."""


class SessionService:
    """Coordinate session persistence and business rules."""

    def __init__(
        self,
        session_repository: SessionRepository,
        skate_spot_repository: SkateSpotRepository,
        activity_service: ActivityService | None = None,
    ) -> None:
        self._sessions = session_repository
        self._spots = skate_spot_repository
        self._activity = activity_service
        self._logger = get_logger(__name__)

    def set_activity_service(self, activity_service: ActivityService) -> None:
        """Set the activity service for recording session events.

        Args:
            activity_service: The ActivityService instance to use for recording activities
        """
        self._activity = activity_service

    def _ensure_spot_exists(self, spot_id: UUID) -> None:
        spot = self._spots.get_by_id(spot_id)
        if spot is None:
            self._logger.warning("session requested for missing spot", spot_id=str(spot_id))
            raise SessionSpotNotFoundError(f"Skate spot with id {spot_id} not found.")

    def get_session(
        self,
        session_id: UUID,
        *,
        current_user_id: str | None = None,
    ) -> Session:
        """Get a session by ID with optional user context for RSVP status.

        Args:
            session_id: The session ID to retrieve
            current_user_id: Optional ID of the current user for personalized data

        Returns:
            The Session object

        Raises:
            SessionNotFoundError: If the session doesn't exist
        """
        session = self._sessions.get_by_id(session_id, current_user_id=current_user_id)
        if session is None:
            self._logger.warning("session not found", session_id=str(session_id))
            raise SessionNotFoundError(f"Session with id {session_id} not found.")
        return session

    def _ensure_session(
        self,
        session_id: UUID,
        *,
        current_user_id: str | None = None,
    ) -> Session:
        """Internal helper that calls get_session(). Kept for backward compatibility."""
        return self.get_session(session_id, current_user_id=current_user_id)

    @staticmethod
    def _ensure_upcoming(start_time: datetime) -> None:
        if start_time < datetime.now(UTC) - timedelta(minutes=5):
            raise ValueError("Sessions must start in the future.")

    @staticmethod
    def _is_organizer(session: Session, user: UserORM) -> bool:
        return str(session.organizer_id) == str(user.id)

    def list_upcoming_sessions(
        self,
        spot_id: UUID,
        *,
        current_user_id: str | None = None,
    ) -> list[Session]:
        """Return upcoming sessions for a skate spot."""

        self._ensure_spot_exists(spot_id)
        sessions = self._sessions.list_upcoming_for_spot(spot_id, current_user_id=current_user_id)
        self._logger.debug(
            "listed upcoming sessions",
            spot_id=str(spot_id),
            session_count=len(sessions),
        )
        return sessions

    def create_session(
        self,
        spot_id: UUID,
        organizer: UserORM,
        payload: SessionCreate,
    ) -> Session:
        """Create a new session for a skate spot."""

        self._ensure_spot_exists(spot_id)
        self._ensure_upcoming(payload.start_time)

        session = self._sessions.create(spot_id, organizer.id, payload)
        self._logger.info(
            "session created",
            session_id=str(session.id),
            spot_id=str(spot_id),
            organizer_id=organizer.id,
        )

        # Record activity for session creation
        if self._activity:
            self._activity.record_session_created(
                user_id=organizer.id,
                session_id=str(session.id),
                session_title=session.title,
            )

        return session

    def update_session(
        self,
        session_id: UUID,
        user: UserORM,
        payload: SessionUpdate,
    ) -> Session:
        """Update a session when permitted."""

        session = self._ensure_session(session_id)

        if not (user.is_admin or self._is_organizer(session, user)):
            self._logger.debug(
                "session update forbidden",
                session_id=str(session_id),
                user_id=user.id,
            )
            raise SessionPermissionError("You are not allowed to modify this session.")

        if session.status != SessionStatus.SCHEDULED and payload.status is None:
            raise SessionInactiveError("Only scheduled sessions can be modified.")

        if payload.start_time is not None:
            self._ensure_upcoming(payload.start_time)

        if payload.status == SessionStatus.SCHEDULED and not user.is_admin:
            raise SessionPermissionError(
                "Only administrators can re-activate cancelled or completed sessions."
            )

        updated = self._sessions.update(session_id, payload)
        if updated is None:
            raise SessionNotFoundError(f"Session with id {session_id} not found.")
        self._logger.info(
            "session updated",
            session_id=str(session_id),
            user_id=user.id,
        )
        return updated

    def change_status(
        self,
        session_id: UUID,
        user: UserORM,
        status: SessionStatus,
    ) -> Session | None:
        """Explicitly set the session status."""

        session = self._ensure_session(session_id)
        if not (user.is_admin or self._is_organizer(session, user)):
            raise SessionPermissionError("You are not allowed to change the session status.")

        updated = self._sessions.set_status(session_id, status)
        if updated is None:
            raise SessionNotFoundError(f"Session with id {session_id} not found.")

        self._logger.info(
            "session status updated",
            session_id=str(session_id),
            status=status.value,
            user_id=user.id,
        )
        return self._sessions.get_by_id(session_id, current_user_id=str(user.id))

    def delete_session(self, session_id: UUID, user: UserORM) -> None:
        """Delete a session entirely."""

        session = self._ensure_session(session_id)
        if not (user.is_admin or self._is_organizer(session, user)):
            raise SessionPermissionError("You are not allowed to delete this session.")

        deleted = self._sessions.delete(session_id)
        if not deleted:
            raise SessionNotFoundError(f"Session with id {session_id} not found.")
        self._logger.info(
            "session deleted",
            session_id=str(session_id),
            user_id=user.id,
        )

    def rsvp_session(
        self,
        session_id: UUID,
        user: UserORM,
        payload: SessionRSVPCreate,
    ) -> Session:
        """Create or update an RSVP for the current user."""

        session = self._ensure_session(session_id, current_user_id=str(user.id))
        if session.status != SessionStatus.SCHEDULED:
            raise SessionInactiveError("Cannot RSVP to a cancelled or completed session.")

        # Ensure timezone awareness for comparison
        end_time = session.end_time
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=UTC)
        if end_time <= datetime.now(UTC):
            raise SessionInactiveError("This session has already finished.")

        existing_response = session.user_response
        if (
            payload.response == SessionResponse.GOING
            and session.capacity is not None
            and session.stats.going >= session.capacity
            and existing_response != SessionResponse.GOING
            and not user.is_admin
        ):
            raise SessionCapacityError("This session has reached capacity.")

        updated_session, rsvp = self._sessions.upsert_rsvp(session_id, user.id, payload)
        self._logger.info(
            "session RSVP recorded",
            session_id=str(session_id),
            user_id=user.id,
            response=payload.response.value,
        )

        # Record activity for RSVP
        if self._activity:
            self._activity.record_session_rsvp(
                user_id=user.id,
                session_id=str(session_id),
                rsvp_id=str(rsvp.id),
                response=payload.response.value,
                session_title=updated_session.title if updated_session else None,
            )

        self._maybe_promote_waitlist(updated_session)
        return self._sessions.get_by_id(session_id, current_user_id=str(user.id))

    def withdraw_rsvp(self, session_id: UUID, user: UserORM) -> Session:
        """Remove the user's RSVP and rebalance the waitlist."""

        self._ensure_session(session_id)
        updated = self._sessions.remove_rsvp(session_id, user.id)
        if updated is None:
            raise SessionRSVPNotFoundError("You do not have an RSVP for this session.")

        self._logger.info(
            "session RSVP withdrawn",
            session_id=str(session_id),
            user_id=user.id,
        )
        self._maybe_promote_waitlist(updated)
        return self._sessions.get_by_id(session_id, current_user_id=str(user.id))

    def _maybe_promote_waitlist(self, session: Session) -> bool:
        """Promote the next waitlisted skater if space is available."""

        if session.capacity is None:
            return False

        if session.stats.going < session.capacity:
            candidate = self._sessions.next_waitlisted(session.id)
            if candidate is None:
                return False
            promoted = self._sessions.promote_waitlisted(candidate.id)
            if promoted is None:
                return False
            self._logger.debug(
                "waitlisted skater promoted",
                session_id=str(session.id),
                user_id=str(candidate.user_id),
            )
            return True
        return False


session_repository = SessionRepository()
_skate_spot_repository = SkateSpotRepository()
session_service = SessionService(session_repository, _skate_spot_repository)


def get_session_service() -> SessionService:
    """FastAPI dependency for session service."""

    return session_service
