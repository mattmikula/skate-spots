"""Repository helpers for skate session scheduling."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import AsyncSessionLocal
from app.db.models import SessionORM, SessionRSVPORM
from app.models.session import (
    Session,
    SessionCreate,
    SessionResponse,
    SessionRSVP,
    SessionRSVPCreate,
    SessionStats,
    SessionStatus,
    SessionUpdate,
)

AsyncSessionFactory = Callable[[], AsyncSession]


def _session_stats(orm_session: SessionORM) -> SessionStats:
    """Return RSVP counts grouped by response type."""

    going = 0
    maybe = 0
    waitlist = 0
    for rsvp in orm_session.rsvps:
        if rsvp.response == SessionResponse.GOING.value:
            going += 1
        elif rsvp.response == SessionResponse.MAYBE.value:
            maybe += 1
        elif rsvp.response == SessionResponse.WAITLIST.value:
            waitlist += 1
    return SessionStats(going=going, maybe=maybe, waitlist=waitlist)


def _session_to_model(orm_session: SessionORM, *, current_user_id: str | None = None) -> Session:
    """Convert an ORM session into its Pydantic representation."""

    stats = _session_stats(orm_session)
    user_response = None
    if current_user_id:
        for rsvp in orm_session.rsvps:
            if rsvp.user_id == current_user_id:
                user_response = SessionResponse(rsvp.response)
                break

    return Session(
        id=UUID(orm_session.id),
        spot_id=UUID(orm_session.spot_id),
        organizer_id=UUID(orm_session.organizer_id),
        organizer_username=(
            orm_session.organizer.username if orm_session.organizer is not None else None
        ),
        title=orm_session.title,
        description=orm_session.description,
        start_time=orm_session.start_time,
        end_time=orm_session.end_time,
        meet_location=orm_session.meet_location,
        skill_level=orm_session.skill_level,
        capacity=orm_session.capacity,
        status=SessionStatus(orm_session.status),
        created_at=orm_session.created_at,
        updated_at=orm_session.updated_at,
        stats=stats,
        user_response=user_response,
    )


def _rsvp_to_model(orm_rsvp: SessionRSVPORM) -> SessionRSVP:
    """Convert an ORM RSVP row into a Pydantic model."""

    return SessionRSVP(
        id=UUID(orm_rsvp.id),
        session_id=UUID(orm_rsvp.session_id),
        user_id=UUID(orm_rsvp.user_id),
        response=SessionResponse(orm_rsvp.response),
        note=orm_rsvp.note,
        created_at=orm_rsvp.created_at,
        updated_at=orm_rsvp.updated_at,
    )


class SessionRepository:
    """Persistence layer for sessions and RSVPs."""

    def __init__(self, session_factory: AsyncSessionFactory | None = None) -> None:
        self._session_factory = session_factory or AsyncSessionLocal

    def _session_select(self, session_id: UUID | str):
        return (
            select(SessionORM)
            .options(
                selectinload(SessionORM.rsvps),
                selectinload(SessionORM.organizer),
            )
            .where(SessionORM.id == str(session_id))
        )

    def _spot_sessions_select(self, spot_id: UUID | str, *, now: datetime):
        return (
            select(SessionORM)
            .options(
                selectinload(SessionORM.rsvps),
                selectinload(SessionORM.organizer),
            )
            .where(SessionORM.spot_id == str(spot_id))
            .where(SessionORM.start_time >= now)
            .order_by(asc(SessionORM.start_time))
        )

    async def get_by_id(
        self,
        session_id: UUID,
        *,
        current_user_id: str | None = None,
    ) -> Session | None:
        """Return a session by its identifier."""

        async with self._session_factory() as db:
            result = await db.execute(self._session_select(session_id))
            orm_session = result.unique().scalar_one_or_none()
            if orm_session is None:
                return None
            return _session_to_model(orm_session, current_user_id=current_user_id)

    async def list_upcoming_for_spot(
        self,
        spot_id: UUID,
        *,
        now: datetime | None = None,
        current_user_id: str | None = None,
    ) -> list[Session]:
        """Return upcoming sessions for a spot."""

        now = now or datetime.now(UTC)
        async with self._session_factory() as db:
            stmt = self._spot_sessions_select(spot_id, now=now)
            result = await db.execute(stmt)
            sessions = result.unique().scalars().all()
            return [
                _session_to_model(session, current_user_id=current_user_id) for session in sessions
            ]

    async def create(
        self,
        spot_id: UUID,
        organizer_id: str,
        payload: SessionCreate,
    ) -> Session:
        """Persist a new session."""

        async with self._session_factory() as db:
            session = SessionORM(
                spot_id=str(spot_id),
                organizer_id=str(organizer_id),
                title=payload.title,
                description=payload.description,
                start_time=payload.start_time,
                end_time=payload.end_time,
                meet_location=payload.meet_location,
                skill_level=payload.skill_level,
                capacity=payload.capacity,
            )
            db.add(session)
            await db.commit()
            result = await db.execute(self._session_select(session.id))
            orm_session = result.unique().scalar_one()
            return _session_to_model(orm_session)

    async def update(self, session_id: UUID, payload: SessionUpdate) -> Session | None:
        """Apply updates to a session."""

        data = payload.model_dump(exclude_unset=True)
        async with self._session_factory() as db:
            result = await db.execute(self._session_select(session_id))
            orm_session = result.unique().scalar_one_or_none()
            if orm_session is None:
                return None

            for field, value in data.items():
                setattr(orm_session, field, value)

            db.add(orm_session)
            await db.commit()
            result = await db.execute(self._session_select(session_id))
            updated_session = result.unique().scalar_one()
            return _session_to_model(updated_session)

    async def set_status(self, session_id: UUID, status: SessionStatus) -> Session | None:
        """Update the status of a session."""

        async with self._session_factory() as db:
            result = await db.execute(self._session_select(session_id))
            orm_session = result.unique().scalar_one_or_none()
            if orm_session is None:
                return None

            orm_session.status = status.value
            db.add(orm_session)
            await db.commit()
            result = await db.execute(self._session_select(session_id))
            updated_session = result.unique().scalar_one()
            return _session_to_model(updated_session)

    async def delete(self, session_id: UUID) -> bool:
        """Delete a session by identifier."""

        async with self._session_factory() as db:
            result = await db.execute(self._session_select(session_id))
            orm_session = result.unique().scalar_one_or_none()
            if orm_session is None:
                return False
            await db.delete(orm_session)
            await db.commit()
            return True

    async def upsert_rsvp(
        self,
        session_id: UUID,
        user_id: str,
        payload: SessionRSVPCreate,
    ) -> tuple[Session, SessionRSVP]:
        """Create or update an RSVP for the user."""

        async with self._session_factory() as db:
            stmt = (
                select(SessionRSVPORM)
                .where(SessionRSVPORM.session_id == str(session_id))
                .where(SessionRSVPORM.user_id == str(user_id))
            )
            result = await db.execute(stmt)
            orm_rsvp = result.scalars().one_or_none()
            if orm_rsvp is None:
                orm_rsvp = SessionRSVPORM(
                    session_id=str(session_id),
                    user_id=str(user_id),
                    response=payload.response.value,
                    note=payload.note,
                )
            else:
                orm_rsvp.response = payload.response.value
                orm_rsvp.note = payload.note

            db.add(orm_rsvp)
            await db.commit()
            await db.refresh(orm_rsvp)
            session_result = await db.execute(self._session_select(session_id))
            orm_session = session_result.unique().scalar_one()
            return _session_to_model(orm_session, current_user_id=str(user_id)), _rsvp_to_model(
                orm_rsvp
            )

    async def remove_rsvp(self, session_id: UUID, user_id: str) -> Session | None:
        """Remove an RSVP and return the updated session."""

        async with self._session_factory() as db:
            stmt = (
                select(SessionRSVPORM)
                .where(SessionRSVPORM.session_id == str(session_id))
                .where(SessionRSVPORM.user_id == str(user_id))
            )
            result = await db.execute(stmt)
            orm_rsvp = result.scalars().one_or_none()
            if orm_rsvp is None:
                return None

            await db.delete(orm_rsvp)
            await db.commit()

            session_result = await db.execute(self._session_select(session_id))
            orm_session = session_result.unique().scalar_one()
            return _session_to_model(orm_session)

    async def next_waitlisted(self, session_id: UUID) -> SessionRSVP | None:
        """Return the oldest waitlisted RSVP."""

        async with self._session_factory() as db:
            stmt = (
                select(SessionRSVPORM)
                .where(SessionRSVPORM.session_id == str(session_id))
                .where(SessionRSVPORM.response == SessionResponse.WAITLIST.value)
                .order_by(asc(SessionRSVPORM.created_at))
            )
            result = await db.execute(stmt)
            orm_rsvp = result.scalars().first()
            return _rsvp_to_model(orm_rsvp) if orm_rsvp else None

    async def promote_waitlisted(self, rsvp_id: UUID) -> Session | None:
        """Promote a waitlisted RSVP to going."""

        async with self._session_factory() as db:
            stmt = select(SessionRSVPORM).where(SessionRSVPORM.id == str(rsvp_id))
            result = await db.execute(stmt)
            orm_rsvp = result.scalars().one_or_none()
            if orm_rsvp is None:
                return None

            orm_rsvp.response = SessionResponse.GOING.value
            db.add(orm_rsvp)
            await db.commit()

            session_result = await db.execute(self._session_select(UUID(orm_rsvp.session_id)))
            orm_session = session_result.unique().scalar_one()
            return _session_to_model(orm_session)
