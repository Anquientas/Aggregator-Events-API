import datetime
from dataclasses import dataclass


@dataclass(slots=True)
class Place:
    id: str
    name: str
    city: str
    address: str
    seats_pattern: str | None = None


@dataclass(slots=True)
class Event:
    id: str
    name: str
    place: Place
    event_time: datetime.datetime
    registration_deadline: datetime.datetime
    status: str
    number_of_visitors: int
    changed_at: datetime.datetime


@dataclass(slots=True)
class Ticket:
    id: str
    provider_ticket_id: str
    event_id: str
    first_name: str
    last_name: str
    email: str
    seat: str
    cancelled: bool = False


@dataclass(slots=True)
class SyncState:
    last_sync_time: datetime.datetime | None
    last_changed_at: datetime.datetime | None
    sync_status: str
    last_error: str | None = None
