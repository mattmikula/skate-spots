"""add spot photos table"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0005_add_spot_photos"
down_revision = "0004_add_favorite_spots"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
            "uploader_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_spot_photos_spot_id", "spot_photos", ["spot_id"])
    op.create_index("ix_spot_photos_uploader_id", "spot_photos", ["uploader_id"])


def downgrade() -> None:
    op.drop_index("ix_spot_photos_uploader_id", table_name="spot_photos")
    op.drop_index("ix_spot_photos_spot_id", table_name="spot_photos")
    op.drop_table("spot_photos")
