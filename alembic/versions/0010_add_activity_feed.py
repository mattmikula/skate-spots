"""Add activity feed table for tracking user actions."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0010_add_activity_feed"
down_revision = "0009_add_user_follows"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""

    op.create_table(
        "activity_feed",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("activity_type", sa.String(length=50), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("activity_metadata", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_activity_feed_user_id", "user_id"),
        sa.Index("ix_activity_feed_created_at", "created_at"),
        sa.Index("ix_activity_feed_activity_type", "activity_type"),
        sa.CheckConstraint(
            "activity_type IN ('spot_created', 'spot_rated', 'spot_commented', 'spot_favorited', 'session_created', 'session_rsvp')",
            name="ck_activity_feed_activity_type",
        ),
        sa.CheckConstraint(
            "target_type IN ('spot', 'rating', 'comment', 'favorite', 'session', 'rsvp')",
            name="ck_activity_feed_target_type",
        ),
    )


def downgrade() -> None:
    """Revert the migration."""

    op.drop_table("activity_feed")
