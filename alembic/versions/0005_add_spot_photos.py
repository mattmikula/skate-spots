"""Add spot photos table for storing uploaded images."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0005_add_spot_photos"
down_revision = "0004_add_favorite_spots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the spot_photos table."""

    op.create_table(
        "spot_photos",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column(
            "spot_id",
            sa.String(length=36),
            sa.ForeignKey("skate_spots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("caption", sa.String(length=500), nullable=True),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_spot_photos_spot_id"), "spot_photos", ["spot_id"])
    op.create_index(op.f("ix_spot_photos_user_id"), "spot_photos", ["user_id"])


def downgrade() -> None:
    """Drop the spot_photos table."""

    op.drop_index(op.f("ix_spot_photos_user_id"), table_name="spot_photos")
    op.drop_index(op.f("ix_spot_photos_spot_id"), table_name="spot_photos")
    op.drop_table("spot_photos")
