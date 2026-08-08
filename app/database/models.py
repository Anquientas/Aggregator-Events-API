import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.outbox import OutboxStatus, OutboxTypes
from app.constants.sync import SyncStatus
from app.database.engine import Base


class Place(Base):
    __tablename__ = "places"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True
    )
    name: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(512))
    seats_pattern: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True
    )

    events: Mapped[list["Event"]] = relationship(back_populates="place")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True
    )
    name: Mapped[str] = mapped_column(String(512))
    place_id: Mapped[str] = mapped_column(ForeignKey("places.id"))
    event_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True)
    )
    registration_deadline: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True)
    )
    status: Mapped[str] = mapped_column(String(32))
    number_of_visitors: Mapped[int] = mapped_column(
        Integer,
        default=0
    )
    changed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True)
    )

    place: Mapped[Place] = relationship(back_populates="events")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="event")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda:
        str(uuid.uuid4())
    )
    provider_ticket_id: Mapped[str] = mapped_column(
        String(64),
        index=True
    )
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"))
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    seat: Mapped[str] = mapped_column(String(32))
    cancelled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC)
    )

    event: Mapped[Event] = relationship(back_populates="tickets")


class SyncMetadata(Base):
    __tablename__ = "sync_metadata"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        default=1
    )
    last_sync_time: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_changed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    sync_status: Mapped[str] = mapped_column(
        String(32),
        default=SyncStatus.idle.value
    )
    last_error: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True
    )

class Outbox(Base):
    __tablename__ = "outbox"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    event_type: Mapped[str] = mapped_column(
        String(64),
        default=OutboxTypes.notification
    )
    payload: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), 'postgresql')
    )
    status: Mapped[str] = mapped_column(
        String(16),
        default=OutboxStatus.pending
    )
    attempts_number: Mapped[int] = mapped_column(
        Integer,
        default=0
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    changed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    error: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True
    )
