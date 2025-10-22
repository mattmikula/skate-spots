"""Add user follow relationships for social features."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0009_add_user_follows"
down_revision = "0008_add_user_profile_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""

    op.create_table(
        "user_follows",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("follower_id", sa.String(length=36), nullable=False),
        sa.Column("following_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["follower_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["following_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "follower_id", "following_id", name="uq_user_follows_follower_following"
        ),
        sa.Index("ix_user_follows_follower_id", "follower_id"),
        sa.Index("ix_user_follows_following_id", "following_id"),
    )


def downgrade() -> None:
    """Revert the migration."""

    op.drop_table("user_follows")
