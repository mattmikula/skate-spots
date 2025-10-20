"""rename spot photo url to file_path and store original filename"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_add_file_metadata_to_spot_photos"
down_revision = "0005_add_spot_photos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("spot_photos") as batch_op:
        batch_op.alter_column(
            "url", new_column_name="file_path", existing_type=sa.String(length=2048)
        )
    with op.batch_alter_table("spot_photos") as batch_op:
        batch_op.alter_column(
            "file_path", existing_type=sa.String(length=2048), type_=sa.String(length=512)
        )
        batch_op.add_column(sa.Column("original_filename", sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("spot_photos") as batch_op:
        batch_op.drop_column("original_filename")
        batch_op.alter_column(
            "file_path", existing_type=sa.String(length=512), type_=sa.String(length=2048)
        )
    with op.batch_alter_table("spot_photos") as batch_op:
        batch_op.alter_column(
            "file_path", new_column_name="url", existing_type=sa.String(length=2048)
        )
