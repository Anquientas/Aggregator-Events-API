"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "places",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=512), nullable=False),
        sa.Column("seats_pattern", sa.String(length=512), nullable=True),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column(
            "place_id",
            sa.String(length=64),
            sa.ForeignKey("places.id"),
            nullable=False,
        ),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registration_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("number_of_visitors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_events_changed_at", "events", ["changed_at"])
    op.create_index("ix_events_event_time", "events", ["event_time"])

    op.create_table(
        "tickets",
        sa.Column("id", sa.String(length=64), primary_key=True),
        # Не unique: провайдер может вернуть тот же ticket_id повторно, если
        # место освободилось (отмена) и было заново забронировано.
        sa.Column("provider_ticket_id", sa.String(length=64), nullable=False, index=True),
        sa.Column(
            "event_id",
            sa.String(length=64),
            sa.ForeignKey("events.id"),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(length=255), nullable=False),
        sa.Column("last_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("seat", sa.String(length=32), nullable=False),
        sa.Column("cancelled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "sync_metadata",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("last_sync_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_status", sa.String(length=32), nullable=False, server_default="idle"),
        sa.Column("last_error", sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("sync_metadata")
    op.drop_table("tickets")
    op.drop_index("ix_events_event_time", table_name="events")
    op.drop_index("ix_events_changed_at", table_name="events")
    op.drop_table("events")
    op.drop_table("places")
