"""Add cached weather snapshots for skate spots."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0014_add_weather_snapshots"
down_revision = "0013_add_spot_check_ins"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create weather snapshot table."""

    op.create_table(
        "weather_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("spot_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="open-meteo"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["spot_id"], ["skate_spots.id"], ondelete="CASCADE"),
    )
    op.create_unique_constraint("uq_weather_snapshots_spot_id", "weather_snapshots", ["spot_id"])
    op.create_index(
        "ix_weather_snapshots_spot_id",
        "weather_snapshots",
        ["spot_id"],
        unique=False,
    )
    op.create_index("ix_weather_snapshots_expires_at", "weather_snapshots", ["expires_at"])
    op.create_index("ix_weather_snapshots_fetched_at", "weather_snapshots", ["fetched_at"])


def downgrade() -> None:
    """Drop weather snapshot table."""

    op.drop_index("ix_weather_snapshots_fetched_at", table_name="weather_snapshots")
    op.drop_index("ix_weather_snapshots_expires_at", table_name="weather_snapshots")
    op.drop_index("ix_weather_snapshots_spot_id", table_name="weather_snapshots")
    op.drop_constraint("uq_weather_snapshots_spot_id", "weather_snapshots", type_="unique")
    op.drop_table("weather_snapshots")
