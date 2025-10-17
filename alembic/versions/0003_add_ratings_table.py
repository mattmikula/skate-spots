"""Add ratings table for skate spots."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0003_add_ratings_table"
down_revision = "0002_add_user_authentication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create ratings table with foreign keys and indexes."""
    op.create_table(
        "ratings",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("spot_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),  # 1-5 star rating
        sa.Column("review", sa.String(length=500), nullable=True),
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
    )

    # Create indexes for efficient querying
    op.create_index(op.f("ix_ratings_spot_id"), "ratings", ["spot_id"])
    op.create_index(op.f("ix_ratings_user_id"), "ratings", ["user_id"])
    op.create_index(
        "ix_ratings_spot_user",
        "ratings",
        ["spot_id", "user_id"],
        unique=True,
    )

    # Create foreign key constraints (using batch mode for SQLite compatibility)
    with op.batch_alter_table("ratings", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_ratings_spot_id_skate_spots",
            "skate_spots",
            ["spot_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "fk_ratings_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Drop ratings table and constraints."""
    # Drop indexes first
    op.drop_index("ix_ratings_spot_user", table_name="ratings")
    op.drop_index(op.f("ix_ratings_user_id"), table_name="ratings")
    op.drop_index(op.f("ix_ratings_spot_id"), table_name="ratings")

    # Drop constraints using batch mode for SQLite compatibility
    with op.batch_alter_table("ratings", schema=None) as batch_op:
        batch_op.drop_constraint("fk_ratings_user_id_users", type_="foreignkey")
        batch_op.drop_constraint("fk_ratings_spot_id_skate_spots", type_="foreignkey")

    op.drop_table("ratings")
