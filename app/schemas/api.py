import datetime

from pydantic import BaseModel, EmailStr, Field

from app.constants.health import HealthStatus
from app.constants.sync import SyncTriggerStatus


class PlaceShort(BaseModel):
    id: str
    name: str
    city: str
    address: str


class PlaceDetail(PlaceShort):
    seats_pattern: str | None = None


class EventListItem(BaseModel):
    id: str
    name: str
    place: PlaceShort
    event_time: datetime.datetime
    registration_deadline: datetime.datetime
    status: str
    number_of_visitors: int


class EventDetail(BaseModel):
    id: str
    name: str
    place: PlaceDetail
    event_time: datetime.datetime
    registration_deadline: datetime.datetime
    status: str
    number_of_visitors: int


class EventListResponse(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[EventListItem]


class SeatsResponse(BaseModel):
    event_id: str
    available_seats: list[str]


class CreateTicketRequest(BaseModel):
    event_id: str
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    seat: str = Field(min_length=1, max_length=32)
    idempotency_key: str | None = Field(default=None, max_length=128)


class CreateTicketResponse(BaseModel):
    ticket_id: str


class CancelTicketResponse(BaseModel):
    success: bool


class HealthResponse(BaseModel):
    status: HealthStatus = HealthStatus.ok


class SyncTriggerResponse(BaseModel):
    status: SyncTriggerStatus = SyncTriggerStatus.triggered
