"""Add favourite skate spots association table."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0004_add_favorite_spots"
down_revision = "0003_add_spot_ratings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the favourite_spots association table."""

    op.create_table(
        "favorite_spots",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "spot_id",
            sa.String(length=36),
            sa.ForeignKey("skate_spots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "spot_id", name="uq_favorite_user_spot"),
    )
    op.create_index(op.f("ix_favorite_spots_user_id"), "favorite_spots", ["user_id"])
    op.create_index(op.f("ix_favorite_spots_spot_id"), "favorite_spots", ["spot_id"])


def downgrade() -> None:
    """Drop the favourite_spots association table."""

    op.drop_index(op.f("ix_favorite_spots_spot_id"), table_name="favorite_spots")
    op.drop_index(op.f("ix_favorite_spots_user_id"), table_name="favorite_spots")
    op.drop_table("favorite_spots")
