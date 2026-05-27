"""add video recordings

Revision ID: 7b3a2c91e405
Revises: 2416e73489fa
Create Date: 2026-05-27 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7b3a2c91e405"
down_revision = "2416e73489fa"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "video_recordings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("bucket", sa.String(length=255), nullable=False),
        sa.Column("object_key", sa.String(length=1024), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_video_recordings_recorded_at",
        "video_recordings",
        ["recorded_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_video_recordings_recorded_at", table_name="video_recordings")
    op.drop_table("video_recordings")
