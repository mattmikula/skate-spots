"""Add user profile fields for bio, avatar, and location."""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_add_user_profile_fields"
down_revision = "0007_add_spot_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add bio, avatar_url, and location columns to users table."""
    op.add_column("users", sa.Column("bio", sa.String(length=500), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=500), nullable=True))
    op.add_column("users", sa.Column("location", sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Remove bio, avatar_url, and location columns from users table."""
    op.drop_column("users", "location")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "bio")
