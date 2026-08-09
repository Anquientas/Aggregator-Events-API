"""Add idempotency_key to tickets table

Revision ID: df0c98e49528
Revises: 555ae0c37a25
Create Date: 2026-08-08 21:20:54.752633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df0c98e49528'
down_revision: Union[str, None] = '555ae0c37a25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "tickets",
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_tickets_idempotency_key",
        "tickets",
        ["idempotency_key"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_tickets_idempotency_key", table_name="tickets")
    op.drop_column("tickets", "idempotency_key")