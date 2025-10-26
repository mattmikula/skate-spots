"""Add real-time spot check-ins."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0013_add_spot_check_ins"
down_revision = "0012_add_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create spot check-in table and extend activity/notification enums."""

    op.create_table(
        "spot_check_ins",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("spot_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="arrived",
        ),
        sa.Column("message", sa.String(length=280), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
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
            "status IN ('heading', 'arrived')",
            name="ck_spot_check_ins_status",
        ),
    )
    op.create_index(
        "ix_spot_check_ins_spot_id_expires_at",
        "spot_check_ins",
        ["spot_id", "expires_at"],
    )
    op.create_index("ix_spot_check_ins_user_id", "spot_check_ins", ["user_id"])

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

    with op.batch_alter_table("notifications", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_notifications_type", type_="check")
        batch_op.create_check_constraint(
            "ck_notifications_type",
            "notification_type IN ('spot_created', 'spot_rated', 'spot_commented', 'spot_favorited', 'spot_checked_in', 'session_created', 'session_rsvp')",
        )


def downgrade() -> None:
    """Revert spot check-in support."""

    with op.batch_alter_table("notifications", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_notifications_type", type_="check")
        batch_op.create_check_constraint(
            "ck_notifications_type",
            "notification_type IN ('spot_created', 'spot_rated', 'spot_commented', 'spot_favorited', 'session_created', 'session_rsvp')",
        )

    with op.batch_alter_table("activity_feed", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_activity_feed_activity_type", type_="check")
        batch_op.drop_constraint("ck_activity_feed_target_type", type_="check")
        batch_op.create_check_constraint(
            "ck_activity_feed_activity_type",
            "activity_type IN ('spot_created', 'spot_rated', 'spot_commented', 'spot_favorited', 'session_created', 'session_rsvp')",
        )
        batch_op.create_check_constraint(
            "ck_activity_feed_target_type",
            "target_type IN ('spot', 'rating', 'comment', 'favorite', 'session', 'rsvp')",
        )

    op.drop_index("ix_spot_check_ins_user_id", table_name="spot_check_ins")
    op.drop_index("ix_spot_check_ins_spot_id_expires_at", table_name="spot_check_ins")
    op.drop_table("spot_check_ins")
