"""Repository layer for skate spots backed by SQLite."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import RatingORM, SkateSpotORM, SpotPhotoORM
from app.models.rating import RatingSummary
from app.models.skate_spot import (
    Difficulty,
    Location,
    SkateSpot,
    SkateSpotCreate,
    SkateSpotFilters,
    SkateSpotUpdate,
    SpotPhoto,
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


def _orm_to_pydantic(
    orm_spot: SkateSpotORM,
    summary: RatingSummary | None = None,
) -> SkateSpot:
    """Convert an ORM instance into a Pydantic model, including rating metadata."""

    rating_summary = summary or RatingSummary(average_score=None, ratings_count=0)
    photos = [
        SpotPhoto(
            id=UUID(photo.id),
            path=photo.file_path,
            original_filename=photo.original_filename,
            created_at=photo.created_at,
        )
        for photo in sorted(orm_spot.photos, key=lambda record: record.created_at)
    ]
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
        average_rating=rating_summary.average_score,
        ratings_count=rating_summary.ratings_count,
        photos=photos,
    )


def _filters_to_conditions(filters: SkateSpotFilters | None) -> list[Any]:
    """Translate ``SkateSpotFilters`` into SQLAlchemy filter conditions."""

    if not filters or not filters.has_filters():
        return []

    conditions: list[Any] = []

    if filters.search:
        pattern = f"%{filters.search.lower()}%"
        conditions.append(
            or_(
                func.lower(SkateSpotORM.name).like(pattern),
                func.lower(SkateSpotORM.description).like(pattern),
                func.lower(SkateSpotORM.city).like(pattern),
                func.lower(SkateSpotORM.country).like(pattern),
            )
        )

    if filters.spot_types:
        conditions.append(
            SkateSpotORM.spot_type.in_([spot_type.value for spot_type in filters.spot_types])
        )

    if filters.difficulties:
        conditions.append(
            SkateSpotORM.difficulty.in_([difficulty.value for difficulty in filters.difficulties])
        )

    if filters.city:
        conditions.append(func.lower(SkateSpotORM.city) == filters.city.lower())

    if filters.country:
        conditions.append(func.lower(SkateSpotORM.country) == filters.country.lower())

    if filters.is_public is not None:
        conditions.append(SkateSpotORM.is_public == filters.is_public)

    if filters.requires_permission is not None:
        conditions.append(SkateSpotORM.requires_permission == filters.requires_permission)

    return conditions


def _haversine_distance(center_lat: float, center_lng: float) -> tuple[Any, Any]:
    """Return great-circle distance expression and ordering clause for nearby queries.

    Returns a tuple of (distance_expression, distance_column) to compute distance
    between two coordinate pairs using the spherical law of cosines for SQLite.

    Note: Despite the function name, this uses the spherical law of cosines
    formula rather than the true Haversine formula for better performance with
    SQLite's trigonometric functions while maintaining sufficient accuracy.

    Args:
        center_lat: Center point latitude in degrees
        center_lng: Center point longitude in degrees

    Returns:
        Tuple of (distance_expression, distance_column) for use in SQLAlchemy queries
    """
    # Spherical law of cosines formula for great-circle distance:
    # d = R * acos(cos(lat1) * cos(lat2) * cos(lng2 - lng1) + sin(lat1) * sin(lat2))
    # Earth's radius in kilometers
    earth_radius_km = 6371

    # Convert degrees to radians for trigonometric functions
    lat1_rad = func.radians(center_lat)
    lng1_rad = func.radians(center_lng)
    lat2_rad = func.radians(SkateSpotORM.latitude)
    lng2_rad = func.radians(SkateSpotORM.longitude)

    # Spherical law of cosines using SQLite trigonometric functions
    distance_expr = earth_radius_km * func.acos(
        func.cos(lat1_rad) * func.cos(lat2_rad) * func.cos(lng2_rad - lng1_rad)
        + func.sin(lat1_rad) * func.sin(lat2_rad)
    )

    return distance_expr, distance_expr.label("distance_km")


class SkateSpotRepository:
    """Repository handling database persistence for skate spots."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or SessionLocal

    def create(self, spot_data: SkateSpotCreate, user_id: str) -> SkateSpot:
        """Create a new skate spot."""

        payload = spot_data.model_dump()
        photo_payloads = payload.pop("photos", [])
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
            session.flush()
            for photo in photo_payloads:
                session.add(
                    SpotPhotoORM(
                        spot_id=orm_spot.id,
                        uploader_id=user_id,
                        file_path=str(photo["path"]),
                        original_filename=photo.get("original_filename"),
                    )
                )
            session.commit()
            session.refresh(orm_spot)
            _ = list(orm_spot.photos)
            return _orm_to_pydantic(
                orm_spot,
                summary=RatingSummary(average_score=None, ratings_count=0),
            )

    def get_by_id(self, spot_id: UUID) -> SkateSpot | None:
        """Get a skate spot by ID."""

        with self._session_factory() as session:
            orm_spot = session.get(SkateSpotORM, str(spot_id))
            if orm_spot is None:
                return None
            summary = self._rating_summary_for_spots(session, [str(spot_id)]).get(
                str(spot_id), RatingSummary(average_score=None, ratings_count=0)
            )
            return _orm_to_pydantic(orm_spot, summary=summary)

    def get_all(self, filters: SkateSpotFilters | None = None) -> list[SkateSpot]:
        """Get all skate spots, optionally filtering by provided criteria."""

        with self._session_factory() as session:
            stmt = select(SkateSpotORM)

            conditions = _filters_to_conditions(filters)
            if conditions:
                stmt = stmt.where(*conditions)

            spots = session.scalars(stmt).all()
            return self._with_rating_summaries(session, spots)

    def get_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        filters: SkateSpotFilters | None = None,
    ) -> list[SkateSpot]:
        """Get skate spots within specified radius, optionally filtering by criteria.

        Uses the spherical law of cosines formula to calculate great-circle distances.

        Args:
            latitude: Center point latitude in degrees
            longitude: Center point longitude in degrees
            radius_km: Search radius in kilometers
            filters: Optional filters to apply in addition to distance

        Returns:
            List of SkateSpot models sorted by distance (closest first)
        """
        with self._session_factory() as session:
            distance_expr, distance_col = _haversine_distance(latitude, longitude)

            stmt = select(SkateSpotORM, distance_col).order_by(distance_expr.asc())

            # Filter by radius
            stmt = stmt.where(distance_expr <= radius_km)

            # Apply additional filters
            conditions = _filters_to_conditions(filters)
            if conditions:
                stmt = stmt.where(*conditions)

            # Execute query and extract results
            results = session.execute(stmt).all()
            if not results:
                return []

            # Extract ORM objects and distances
            orm_spots = [row[0] for row in results]
            distances = {row[0].id: row[1] for row in results}

            # Get rating summaries
            enriched = self._with_rating_summaries(session, orm_spots)

            # Add distance information to each spot
            for spot in enriched:
                spot.distance_km = distances.get(str(spot.id))

            return enriched

    def get_many_by_ids(self, spot_ids: list[UUID]) -> list[SkateSpot]:
        """Return skate spots matching the provided identifiers."""

        if not spot_ids:
            return []

        with self._session_factory() as session:
            normalised_ids = [str(spot_id) for spot_id in spot_ids]
            stmt = select(SkateSpotORM).where(SkateSpotORM.id.in_(normalised_ids))
            spots = session.scalars(stmt).all()
            enriched = self._with_rating_summaries(session, spots)
            spot_map = {str(spot.id): spot for spot in enriched}
            return [spot_map[spot_id] for spot_id in normalised_ids if spot_id in spot_map]

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
                elif field == "photos" and value is not None:
                    session.query(SpotPhotoORM).filter(SpotPhotoORM.spot_id == orm_spot.id).delete(
                        synchronize_session=False
                    )
                    for photo in value:
                        session.add(
                            SpotPhotoORM(
                                spot_id=orm_spot.id,
                                uploader_id=orm_spot.user_id,
                                file_path=str(photo["path"]),
                                original_filename=photo.get("original_filename"),
                            )
                        )
                else:
                    setattr(orm_spot, field, _enum_to_value(value))

            orm_spot.updated_at = datetime.now(UTC)
            session.add(orm_spot)
            session.commit()
            session.refresh(orm_spot)
            _ = list(orm_spot.photos)
            summary = self._rating_summary_for_spots(session, [str(spot_id)]).get(
                str(spot_id), RatingSummary(average_score=None, ratings_count=0)
            )
            return _orm_to_pydantic(orm_spot, summary=summary)

    def delete(self, spot_id: UUID) -> bool:
        """Delete a skate spot by ID."""

        with self._session_factory() as session:
            orm_spot = session.get(SkateSpotORM, str(spot_id))
            if orm_spot is None:
                return False
            session.delete(orm_spot)
            session.commit()
            return True

    def _with_rating_summaries(
        self,
        session: Session,
        spots: list[SkateSpotORM],
    ) -> list[SkateSpot]:
        """Return hydrated ``SkateSpot`` models for the provided ORM instances."""

        if not spots:
            return []

        spot_ids = [spot.id for spot in spots]
        summaries = self._rating_summary_for_spots(session, spot_ids)
        return [
            _orm_to_pydantic(
                spot,
                summary=summaries.get(spot.id, RatingSummary(average_score=None, ratings_count=0)),
            )
            for spot in spots
        ]

    def _rating_summary_for_spots(
        self,
        session: Session,
        spot_ids: list[str],
    ) -> dict[str, RatingSummary]:
        """Return a mapping of spot ID to rating summary for the given spot IDs."""

        if not spot_ids:
            return {}

        normalised_ids = [str(spot_id) for spot_id in spot_ids]
        stmt = (
            select(
                RatingORM.spot_id,
                func.count(RatingORM.id),
                func.avg(RatingORM.score),
            )
            .where(RatingORM.spot_id.in_(normalised_ids))
            .group_by(RatingORM.spot_id)
        )

        summaries: dict[str, RatingSummary] = {}
        for spot_id, count, average in session.execute(stmt):
            average_score = round(float(average), 2) if average is not None else None
            count_value = int(count) if count is not None else 0
            summaries[spot_id] = RatingSummary(
                average_score=average_score,
                ratings_count=count_value,
            )
        return summaries
