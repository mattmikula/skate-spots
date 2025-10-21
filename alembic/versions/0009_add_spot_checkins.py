"""Add spot check-ins table for session logging."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0009_add_spot_checkins"
down_revision = "0008_add_user_profile_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""

    op.create_table(
        "spot_checkins",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("spot_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("checked_in_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["spot_id"], ["skate_spots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_spot_checkins_spot_id"), "spot_checkins", ["spot_id"], unique=False)
    op.create_index(op.f("ix_spot_checkins_user_id"), "spot_checkins", ["user_id"], unique=False)


def downgrade() -> None:
    """Revert the migration."""

    op.drop_index(op.f("ix_spot_checkins_user_id"), table_name="spot_checkins")
    op.drop_index(op.f("ix_spot_checkins_spot_id"), table_name="spot_checkins")
    op.drop_table("spot_checkins")
