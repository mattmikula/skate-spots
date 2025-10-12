"""Repository layer for skate spots backed by SQLite."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import SkateSpotORM
from app.models.skate_spot import (
    Difficulty,
    Location,
    SkateSpot,
    SkateSpotCreate,
    SkateSpotUpdate,
    SpotType,
)

SessionFactory = Callable[[], Session]


def _enum_to_value(value: Any) -> Any:
    """Return the underlying value for enums to store in the database."""

    return value.value if hasattr(value, "value") else value


def _location_dict(location: Location | dict[str, Any]) -> dict[str, Any]:
    """Normalise location data into a plain dictionary."""

    if isinstance(location, Location):
        return location.model_dump()
    return dict(location)


def _orm_to_pydantic(orm_spot: SkateSpotORM) -> SkateSpot:
    """Convert an ORM instance into a Pydantic model."""

    return SkateSpot(
        id=UUID(orm_spot.id),
        name=orm_spot.name,
        description=orm_spot.description,
        spot_type=SpotType(orm_spot.spot_type),
        difficulty=Difficulty(orm_spot.difficulty),
        location=Location(
            latitude=orm_spot.latitude,
            longitude=orm_spot.longitude,
            address=orm_spot.address,
            city=orm_spot.city,
            country=orm_spot.country,
        ),
        is_public=orm_spot.is_public,
        requires_permission=orm_spot.requires_permission,
        created_at=orm_spot.created_at,
        updated_at=orm_spot.updated_at,
    )


class SkateSpotRepository:
    """Repository handling database persistence for skate spots."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or SessionLocal

    def create(self, spot_data: SkateSpotCreate, user_id: str) -> SkateSpot:
        """Create a new skate spot."""

        payload = spot_data.model_dump()
        location_data = _location_dict(payload.pop("location"))
        orm_spot = SkateSpotORM(
            **{key: _enum_to_value(value) for key, value in payload.items()},
            latitude=location_data["latitude"],
            longitude=location_data["longitude"],
            address=location_data.get("address"),
            city=location_data["city"],
            country=location_data["country"],
            user_id=user_id,
        )

        with self._session_factory() as session:
            session.add(orm_spot)
            session.commit()
            session.refresh(orm_spot)
            return _orm_to_pydantic(orm_spot)

    def get_by_id(self, spot_id: UUID) -> SkateSpot | None:
        """Get a skate spot by ID."""

        with self._session_factory() as session:
            orm_spot = session.get(SkateSpotORM, str(spot_id))
            if orm_spot is None:
                return None
            return _orm_to_pydantic(orm_spot)

    def get_all(self) -> list[SkateSpot]:
        """Get all skate spots."""

        with self._session_factory() as session:
            spots = session.scalars(select(SkateSpotORM)).all()
            return [_orm_to_pydantic(spot) for spot in spots]

    def is_owner(self, spot_id: UUID, user_id: str) -> bool:
        """Check if a user owns a skate spot."""

        with self._session_factory() as session:
            orm_spot = session.get(SkateSpotORM, str(spot_id))
            if orm_spot is None:
                return False
            return orm_spot.user_id == user_id

    def update(self, spot_id: UUID, update_data: SkateSpotUpdate) -> SkateSpot | None:
        """Update an existing skate spot."""

        updates = update_data.model_dump(exclude_unset=True)

        with self._session_factory() as session:
            orm_spot = session.get(SkateSpotORM, str(spot_id))
            if orm_spot is None:
                return None

            for field, value in updates.items():
                if field == "location" and value is not None:
                    location_data = _location_dict(value)
                    orm_spot.latitude = location_data["latitude"]
                    orm_spot.longitude = location_data["longitude"]
                    orm_spot.address = location_data.get("address")
                    orm_spot.city = location_data["city"]
                    orm_spot.country = location_data["country"]
                else:
                    setattr(orm_spot, field, _enum_to_value(value))

            orm_spot.updated_at = datetime.utcnow()
            session.add(orm_spot)
            session.commit()
            session.refresh(orm_spot)
            return _orm_to_pydantic(orm_spot)

    def delete(self, spot_id: UUID) -> bool:
        """Delete a skate spot by ID."""

        with self._session_factory() as session:
            orm_spot = session.get(SkateSpotORM, str(spot_id))
            if orm_spot is None:
                return False
            session.delete(orm_spot)
            session.commit()
            return True
