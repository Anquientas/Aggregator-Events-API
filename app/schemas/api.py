import datetime

from pydantic import BaseModel, EmailStr, Field

from app.constants.event import EventStatus
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
    status: EventStatus
    number_of_visitors: int


class EventDetail(BaseModel):
    id: str
    name: str
    place: PlaceDetail
    event_time: datetime.datetime
    registration_deadline: datetime.datetime
    status: EventStatus
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
    idempotency_key: str | None = Field(
        default=None,
        max_length=128,
        description=(
            "Необязательный ключ идемпотентности для повторных запросов "
            "(двойной клик, retry на клиенте). Повторный запрос с тем же "
            "ключом и теми же данными (event_id, seat, email, first_name, "
            "last_name) вернёт 201 с тем же ticket_id, не создавая новый "
            "билет и не обращаясь повторно к Events Provider. Запрос с "
            "тем же ключом, но другими данными — 409 Conflict. Без ключа "
            "каждый запрос всегда обрабатывается как новый."
        ),
    )


class CreateTicketResponse(BaseModel):
    ticket_id: str


class CancelTicketResponse(BaseModel):
    success: bool


class HealthResponse(BaseModel):
    status: HealthStatus = HealthStatus.ok


class SyncTriggerResponse(BaseModel):
    status: SyncTriggerStatus = SyncTriggerStatus.triggered
