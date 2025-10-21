"""Add optional profile fields to the users table."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_add_user_profile_fields"
down_revision = "0007_add_spot_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""

    op.add_column("users", sa.Column("display_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("bio", sa.String(length=500), nullable=True))
    op.add_column("users", sa.Column("location", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("website_url", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("instagram_handle", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("profile_photo_url", sa.String(length=512), nullable=True))


def downgrade() -> None:
    """Revert the migration."""

    op.drop_column("users", "profile_photo_url")
    op.drop_column("users", "instagram_handle")
    op.drop_column("users", "website_url")
    op.drop_column("users", "location")
    op.drop_column("users", "bio")
    op.drop_column("users", "display_name")
