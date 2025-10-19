"""Add table for skate spot comments."""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0007_add_spot_comments"
down_revision = "0006_add_file_metadata_to_spot_photos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "spot_comments",
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
        sa.Column("content", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_spot_comments_spot_id", "spot_comments", ["spot_id"])
    op.create_index("ix_spot_comments_user_id", "spot_comments", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_spot_comments_user_id", table_name="spot_comments")
    op.drop_index("ix_spot_comments_spot_id", table_name="spot_comments")
    op.drop_table("spot_comments")
