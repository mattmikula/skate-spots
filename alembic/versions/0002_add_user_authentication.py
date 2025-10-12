"""Add user authentication and user ownership for skate spots."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

import bcrypt
import sqlalchemy as sa

from alembic import op

revision = "0002_add_user_authentication"
down_revision = "0001_create_skate_spots_table"
branch_labels = None
depends_on = None

_SCHEMA_PREFIX = "bcrypt_sha256$"


def _hash_placeholder(password: str) -> str:
    """Hash placeholder passwords using the bcrypt-sha256 scheme."""

    digest = hashlib.sha256(password.encode("utf-8")).digest()
    hashed = bcrypt.hashpw(digest, bcrypt.gensalt())
    return f"{_SCHEMA_PREFIX}{hashed.decode('utf-8')}"


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "is_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
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
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Add user_id column to skate_spots (nullable while we backfill)
    op.add_column("skate_spots", sa.Column("user_id", sa.String(length=36), nullable=True))
    op.create_index(op.f("ix_skate_spots_user_id"), "skate_spots", ["user_id"])

    bind = op.get_bind()
    skate_spots_without_owner = bind.execute(
        sa.text("SELECT id FROM skate_spots WHERE user_id IS NULL")
    ).fetchall()

    if skate_spots_without_owner:
        system_user_id = str(uuid.uuid4())
        now = datetime.utcnow()

        bind.execute(
            sa.text(
                """
                INSERT INTO users (id, email, username, hashed_password, is_active, is_admin, created_at, updated_at)
                VALUES (:id, :email, :username, :hashed_password, 1, 1, :created_at, :updated_at)
                """
            ),
            {
                "id": system_user_id,
                "email": "legacy-user@example.com",
                "username": "legacy-user",
                "hashed_password": _hash_placeholder("legacy-user-placeholder"),
                "created_at": now,
                "updated_at": now,
            },
        )

        bind.execute(
            sa.text("UPDATE skate_spots SET user_id = :user_id WHERE user_id IS NULL"),
            {"user_id": system_user_id},
        )

    op.alter_column(
        "skate_spots",
        "user_id",
        existing_type=sa.String(length=36),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_skate_spots_user_id_users",
        "skate_spots",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_skate_spots_user_id_users", "skate_spots", type_="foreignkey")
    op.drop_index(op.f("ix_skate_spots_user_id"), table_name="skate_spots")
    op.drop_column("skate_spots", "user_id")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
