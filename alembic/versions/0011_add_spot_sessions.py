"""Add session scheduling tables for skate spots."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0011_add_spot_sessions"
down_revision = "0010_add_activity_feed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create session and RSVP tables."""

    op.create_table(
        "spot_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("spot_id", sa.String(length=36), nullable=False),
        sa.Column("organizer_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("meet_location", sa.String(length=255), nullable=True),
        sa.Column("skill_level", sa.String(length=50), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["spot_id"],
            ["skate_spots.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organizer_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "capacity IS NULL OR capacity >= 1",
            name="ck_spot_sessions_capacity_positive",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'cancelled', 'completed')",
            name="ck_spot_sessions_status_enum",
        ),
    )
    op.create_index(
        "ix_spot_sessions_spot_start_time",
        "spot_sessions",
        ["spot_id", "start_time"],
    )

    op.create_table(
        "session_rsvps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column(
            "response",
            sa.String(length=20),
            nullable=False,
            server_default="going",
        ),
        sa.Column("note", sa.String(length=300), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["spot_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "response IN ('going', 'maybe', 'waitlist')",
            name="ck_session_rsvps_response_enum",
        ),
        sa.UniqueConstraint(
            "session_id",
            "user_id",
            name="uq_session_rsvps_session_user",
        ),
    )
    op.create_index(
        "ix_session_rsvps_session_id",
        "session_rsvps",
        ["session_id"],
    )
    op.create_index(
        "ix_session_rsvps_user_id",
        "session_rsvps",
        ["user_id"],
    )


def downgrade() -> None:
    """Drop session scheduling tables."""

    op.drop_index("ix_session_rsvps_user_id", table_name="session_rsvps")
    op.drop_index("ix_session_rsvps_session_id", table_name="session_rsvps")
    op.drop_table("session_rsvps")
    op.drop_index("ix_spot_sessions_spot_start_time", table_name="spot_sessions")
    op.drop_table("spot_sessions")
