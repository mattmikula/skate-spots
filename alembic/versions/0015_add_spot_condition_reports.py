"""Add spot condition reports."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0015_add_spot_condition_reports"
down_revision = "0014_add_weather_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create spot condition reports table and extend activity/notification enums."""

    op.create_table(
        "spot_condition_reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("spot_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("surface_quality", sa.String(length=20), nullable=True),
        sa.Column("crowdedness", sa.String(length=20), nullable=True),
        sa.Column("security", sa.String(length=20), nullable=True),
        sa.Column("overall_status", sa.String(length=20), nullable=False),
        sa.Column("note", sa.String(length=280), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
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
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "surface_quality IN ('excellent', 'good', 'fair', 'poor', 'terrible')",
            name="ck_spot_condition_reports_surface_quality",
        ),
        sa.CheckConstraint(
            "crowdedness IN ('empty', 'quiet', 'moderate', 'busy', 'packed')",
            name="ck_spot_condition_reports_crowdedness",
        ),
        sa.CheckConstraint(
            "security IN ('clear', 'relaxed', 'watchful', 'strict', 'hostile')",
            name="ck_spot_condition_reports_security",
        ),
        sa.CheckConstraint(
            "overall_status IN ('prime', 'good', 'okay', 'rough', 'closed')",
            name="ck_spot_condition_reports_overall_status",
        ),
    )
    op.create_index(
        "ix_spot_condition_reports_spot_id_expires_at",
        "spot_condition_reports",
        ["spot_id", "expires_at"],
    )
    op.create_index("ix_spot_condition_reports_user_id", "spot_condition_reports", ["user_id"])

    # Update activity_feed constraints to include new activity type
    with op.batch_alter_table("activity_feed", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_activity_feed_activity_type", type_="check")
        batch_op.drop_constraint("ck_activity_feed_target_type", type_="check")
        batch_op.create_check_constraint(
            "ck_activity_feed_activity_type",
            "activity_type IN ('spot_created', 'spot_rated', 'spot_commented', 'spot_favorited', 'spot_checked_in', 'spot_condition_reported', 'session_created', 'session_rsvp')",
        )
        batch_op.create_check_constraint(
            "ck_activity_feed_target_type",
            "target_type IN ('spot', 'rating', 'comment', 'favorite', 'check_in', 'condition_report', 'session', 'rsvp')",
        )

    # Update notifications constraints to include new notification type
    with op.batch_alter_table("notifications", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_notifications_type", type_="check")
        batch_op.create_check_constraint(
            "ck_notifications_type",
            "notification_type IN ('spot_created', 'spot_rated', 'spot_commented', 'spot_favorited', 'spot_checked_in', 'spot_condition_reported', 'session_created', 'session_rsvp')",
        )


def downgrade() -> None:
    """Revert spot condition reports support."""

    # Revert notifications constraint
    with op.batch_alter_table("notifications", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_notifications_type", type_="check")
        batch_op.create_check_constraint(
            "ck_notifications_type",
            "notification_type IN ('spot_created', 'spot_rated', 'spot_commented', 'spot_favorited', 'spot_checked_in', 'session_created', 'session_rsvp')",
        )

    # Revert activity_feed constraints
    with op.batch_alter_table("activity_feed", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_activity_feed_activity_type", type_="check")
        batch_op.drop_constraint("ck_activity_feed_target_type", type_="check")
        batch_op.create_check_constraint(
            "ck_activity_feed_activity_type",
            "activity_type IN ('spot_created', 'spot_rated', 'spot_commented', 'spot_favorited', 'spot_checked_in', 'session_created', 'session_rsvp')",
        )
        batch_op.create_check_constraint(
            "ck_activity_feed_target_type",
            "target_type IN ('spot', 'rating', 'comment', 'favorite', 'check_in', 'session', 'rsvp')",
        )

    # Drop indexes and table
    op.drop_index("ix_spot_condition_reports_user_id", table_name="spot_condition_reports")
    op.drop_index(
        "ix_spot_condition_reports_spot_id_expires_at", table_name="spot_condition_reports"
    )
    op.drop_table("spot_condition_reports")
