"""Add spot ratings table to support user-managed ratings."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0003_add_spot_ratings"
down_revision = "0002_add_user_authentication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "spot_ratings",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("spot_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("score BETWEEN 1 AND 5", name="ck_spot_ratings_score_range"),
        sa.UniqueConstraint("spot_id", "user_id", name="uq_spot_ratings_user_spot"),
    )
    op.create_index(op.f("ix_spot_ratings_spot_id"), "spot_ratings", ["spot_id"], unique=False)
    op.create_index(op.f("ix_spot_ratings_user_id"), "spot_ratings", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_spot_ratings_spot_id_skate_spots",
        "spot_ratings",
        "skate_spots",
        ["spot_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_spot_ratings_user_id_users",
        "spot_ratings",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_spot_ratings_user_id_users", "spot_ratings", type_="foreignkey")
    op.drop_constraint("fk_spot_ratings_spot_id_skate_spots", "spot_ratings", type_="foreignkey")
    op.drop_index(op.f("ix_spot_ratings_user_id"), table_name="spot_ratings")
    op.drop_index(op.f("ix_spot_ratings_spot_id"), table_name="spot_ratings")
    op.drop_table("spot_ratings")
