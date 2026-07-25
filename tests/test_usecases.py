import datetime
from unittest.mock import AsyncMock

import pytest

from app.core.cache import TTLCache
from app.core.exceptions import (
    EventAlreadyOccurred,
    EventNotFound,
    EventUnexpectedStatus,
    RegistrationClosed,
    SeatNotAvailable,
    TicketNotFound,
)
from app.core.provider_client import EventsProviderClient
from app.domain.entities import Event, Place, Ticket
from app.usecases.cancel_ticket import CancelTicketUsecase
from app.usecases.create_ticket import CreateTicketUsecase
from app.usecases.enums import EventStatus
from app.usecases.get_seats import GetSeatsUsecase


class FakeEventRepository:
    def __init__(self, events: dict[str, Event] | None = None) -> None:
        self.events = events or {}
        self.visitor_deltas: list[tuple[str, int]] = []

    async def get(self, event_id: str) -> Event | None:
        return self.events.get(event_id)

    async def upsert(self, event: Event) -> None:
        self.events[event.id] = event

    async def list(self, date_from, page, page_size):
        return list(self.events.values()), len(self.events)

    async def increment_visitors(self, event_id: str, delta: int) -> None:
        self.visitor_deltas.append((event_id, delta))
        if event_id in self.events:
            self.events[event_id].number_of_visitors += delta


class FakeTicketRepository:
    def __init__(self, tickets: dict[str, Ticket] | None = None) -> None:
        self.tickets = tickets or {}

    async def create(self, ticket: Ticket) -> None:
        self.tickets[ticket.id] = ticket

    async def get(self, ticket_id: str) -> Ticket | None:
        return self.tickets.get(ticket_id)

    async def mark_cancelled(self, ticket_id: str) -> None:
        if ticket_id in self.tickets:
            self.tickets[ticket_id].cancelled = True


def _make_event(status: str = EventStatus.published) -> Event:
    return Event(
        id="event-1",
        name="Концерт",
        place=Place(
            id="place-1",
            name="Зал",
            city="Москва",
            address="ул. Пушкина"
        ),
        event_time=datetime.datetime(
            2027, 1, 11, 17, 0, tzinfo=datetime.UTC
        ),
        registration_deadline=datetime.datetime(
            2027, 1, 10, 17, 0, tzinfo=datetime.UTC
        ),
        status=status,
        number_of_visitors=5,
        changed_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
    )


async def test_create_ticket_registers_and_persists() -> None:
    events = FakeEventRepository({"event-1": _make_event()})
    tickets = FakeTicketRepository()
    client = AsyncMock(spec=EventsProviderClient)
    client.register.return_value = "provider-ticket-1"

    usecase = CreateTicketUsecase(
        client=client,
        events=events,
        tickets=tickets
    )
    ticket = await usecase.do(
        event_id="event-1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A15",
    )

    assert ticket.provider_ticket_id == "provider-ticket-1"
    assert tickets.tickets[ticket.id] == ticket
    assert events.visitor_deltas == [("event-1", 1)]
    client.register.assert_awaited_once_with(
        event_id="event-1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A15",
    )


async def test_create_ticket_raises_when_event_missing() -> None:
    events = FakeEventRepository({})
    tickets = FakeTicketRepository()
    client = AsyncMock(spec=EventsProviderClient)

    usecase = CreateTicketUsecase(
        client=client,
        events=events,
        tickets=tickets
    )

    with pytest.raises(EventNotFound):
        await usecase.do(
            event_id="missing",
            first_name="Иван",
            last_name="Иванов",
            email="ivan@example.com",
            seat="A15",
        )
    client.register.assert_not_awaited()


async def test_create_ticket_raises_when_event_not_published() -> None:
    events = FakeEventRepository(
        {"event-1": _make_event(status=EventStatus.cancelled)}
    )
    tickets = FakeTicketRepository()
    client = AsyncMock(spec=EventsProviderClient)

    usecase = CreateTicketUsecase(
        client=client,
        events=events,
        tickets=tickets
    )

    with pytest.raises(EventUnexpectedStatus):
        await usecase.do(
            event_id="event-1",
            first_name="Иван",
            last_name="Иванов",
            email="ivan@example.com",
            seat="A15",
        )
    client.register.assert_not_awaited()


async def test_marks_cancelled_and_decrements_visitors() -> None:
    ticket = Ticket(
        id="ticket-1",
        provider_ticket_id="provider-ticket-1",
        event_id="event-1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A15",
    )
    events = FakeEventRepository({"event-1": _make_event()})
    tickets = FakeTicketRepository({"ticket-1": ticket})
    client = AsyncMock(spec=EventsProviderClient)
    client.cancel.return_value = True

    usecase = CancelTicketUsecase(
        client=client,
        events=events,
        tickets=tickets
    )
    success = await usecase.do("ticket-1")

    assert success is True
    assert tickets.tickets["ticket-1"].cancelled is True
    assert events.visitor_deltas == [("event-1", -1)]
    client.cancel.assert_awaited_once_with("event-1", "provider-ticket-1")


async def test_cancel_ticket_raises_when_missing() -> None:
    events = FakeEventRepository()
    tickets = FakeTicketRepository()
    client = AsyncMock(spec=EventsProviderClient)

    usecase = CancelTicketUsecase(
        client=client,
        events=events,
        tickets=tickets
    )

    with pytest.raises(TicketNotFound):
        await usecase.do("missing")
    client.cancel.assert_not_awaited()


async def test_raises_when_registration_deadline_passed() -> None:
    past_deadline_event = Event(
        id="event-1",
        name="Концерт",
        place=Place(
            id="place-1",
            name="Зал",
            city="Москва",
            address="ул. Пушкина"
        ),
        event_time=datetime.datetime(
            2020, 1, 11, 17, 0, tzinfo=datetime.UTC
        ),
        registration_deadline=datetime.datetime(
            2020, 1, 10, 17, 0, tzinfo=datetime.UTC
        ),
        status=EventStatus.published,
        number_of_visitors=5,
        changed_at=datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
    )
    events = FakeEventRepository({"event-1": past_deadline_event})
    tickets = FakeTicketRepository()
    client = AsyncMock(spec=EventsProviderClient)

    usecase = CreateTicketUsecase(
        client=client,
        events=events,
        tickets=tickets
    )

    with pytest.raises(RegistrationClosed):
        await usecase.do(
            event_id="event-1",
            first_name="Иван",
            last_name="Иванов",
            email="ivan@example.com",
            seat="A15",
        )
    client.register.assert_not_awaited()


async def test_raises_seat_not_available_when_provider_rejects() -> None:
    events = FakeEventRepository({"event-1": _make_event()})
    tickets = FakeTicketRepository()
    client = AsyncMock(spec=EventsProviderClient)
    client.register.side_effect = SeatNotAvailable("A15")

    usecase = CreateTicketUsecase(
        client=client,
        events=events,
        tickets=tickets
    )

    with pytest.raises(SeatNotAvailable):
        await usecase.do(
            event_id="event-1",
            first_name="Иван",
            last_name="Иванов",
            email="ivan@example.com",
            seat="A15",
        )
    assert tickets.tickets == {}
    assert events.visitor_deltas == []


async def test_cancel_ticket_raises_when_event_already_occurred() -> None:
    past_event = Event(
        id="event-1",
        name="Концерт",
        place=Place(
            id="place-1",
            name="Зал",
            city="Москва",
            address="ул. Пушкина"
        ),
        event_time=datetime.datetime(
            2020, 1, 11, 17, 0, tzinfo=datetime.UTC
        ),
        registration_deadline=datetime.datetime(
            2020, 1, 10, 17, 0, tzinfo=datetime.UTC
        ),
        status=EventStatus.published,
        number_of_visitors=5,
        changed_at=datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
    )
    ticket = Ticket(
        id="ticket-1",
        provider_ticket_id="provider-ticket-1",
        event_id="event-1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A15",
    )
    events = FakeEventRepository({"event-1": past_event})
    tickets = FakeTicketRepository({"ticket-1": ticket})
    client = AsyncMock(spec=EventsProviderClient)

    usecase = CancelTicketUsecase(
        client=client,
        events=events,
        tickets=tickets
    )

    with pytest.raises(EventAlreadyOccurred):
        await usecase.do("ticket-1")
    client.cancel.assert_not_awaited()


async def test_get_seats_returns_seats_for_published_event() -> None:
    events = FakeEventRepository({"event-1": _make_event()})
    client = AsyncMock(spec=EventsProviderClient)
    client.seats.return_value = ["A1", "A2"]
    cache: TTLCache[list[str]] = TTLCache(timeout=30)

    usecase = GetSeatsUsecase(client=client, events=events, cache=cache)
    seats = await usecase.do("event-1")

    assert seats == ["A1", "A2"]
    client.seats.assert_awaited_once_with("event-1")


async def test_get_seats_uses_cache_on_second_call() -> None:
    events = FakeEventRepository({"event-1": _make_event()})
    client = AsyncMock(spec=EventsProviderClient)
    client.seats.return_value = ["A1", "A2"]
    cache: TTLCache[list[str]] = TTLCache(timeout=30)
    usecase = GetSeatsUsecase(client=client, events=events, cache=cache)

    await usecase.do("event-1")
    await usecase.do("event-1")

    client.seats.assert_awaited_once()  # второй вызов обслужен из кэша


async def test_get_seats_raises_when_event_missing() -> None:
    events = FakeEventRepository({})
    client = AsyncMock(spec=EventsProviderClient)
    cache: TTLCache[list[str]] = TTLCache(timeout=30)

    usecase = GetSeatsUsecase(client=client, events=events, cache=cache)

    with pytest.raises(EventNotFound):
        await usecase.do("missing")
    client.seats.assert_not_awaited()


async def test_get_seats_raises_when_event_not_published() -> None:
    events = FakeEventRepository(
        {"event-1": _make_event(status=EventStatus.new)}
    )
    client = AsyncMock(spec=EventsProviderClient)
    cache: TTLCache[list[str]] = TTLCache(timeout=30)

    usecase = GetSeatsUsecase(client=client, events=events, cache=cache)

    with pytest.raises(EventUnexpectedStatus):
        await usecase.do("event-1")
    client.seats.assert_not_awaited()
