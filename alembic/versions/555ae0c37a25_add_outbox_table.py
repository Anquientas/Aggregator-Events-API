"""add outbox table

Revision ID: 555ae0c37a25
Revises: 0001_initial
Create Date: 2026-08-08 15:08:59.647913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '555ae0c37a25'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "outbox",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "event_type",
            sa.String(length=64),
            nullable=False,
            server_default="notification",
        ),
        sa.Column(
            "payload",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "attempts_number",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("error", sa.String(length=2048), nullable=True),
    )
    op.create_index(
        "ix_outbox_pending", "outbox", ["created_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade():
    op.drop_index("ix_outbox_pending", table_name="outbox")
    op.drop_table("outbox")
