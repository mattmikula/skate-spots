"""Add notifications table for user alerts."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0012_add_notifications"
down_revision = "0011_add_spot_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create notifications table."""

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=True),
        sa.Column("activity_id", sa.String(length=36), nullable=True),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("notification_metadata", sa.Text(), nullable=True),
        sa.Column(
            "is_read",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["activity_id"],
            ["activity_feed.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "notification_type IN ('spot_created', 'spot_rated', 'spot_commented', 'spot_favorited', 'session_created', 'session_rsvp')",
            name="ck_notifications_type",
        ),
    )
    op.create_index(
        "ix_notifications_user_id_is_read_created_at",
        "notifications",
        ["user_id", "is_read", "created_at"],
    )
    op.create_index("ix_notifications_actor_id", "notifications", ["actor_id"])
    op.create_index("ix_notifications_activity_id", "notifications", ["activity_id"])


def downgrade() -> None:
    """Drop notifications table."""

    op.drop_index("ix_notifications_activity_id", table_name="notifications")
    op.drop_index("ix_notifications_actor_id", table_name="notifications")
    op.drop_index("ix_notifications_user_id_is_read_created_at", table_name="notifications")
    op.drop_table("notifications")
