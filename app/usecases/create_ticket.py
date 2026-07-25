import datetime
import uuid

from app.core.exceptions import (
    EventNotFound,
    EventUnexpectedStatus,
    RegistrationClosed,
)
from app.core.provider_client import EventsProviderClient
from app.core.timeutils import ensure_utc
from app.domain.entities import Ticket
from app.repositories.protocols import EventRepository, TicketRepository
from app.usecases.enums import EventStatus


class CreateTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        events: EventRepository,
        tickets: TicketRepository,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets

    async def do(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> Ticket:
        event = await self._events.get(event_id)
        if not event:
            raise EventNotFound(event_id)

        if event.status != EventStatus.published:
            raise EventUnexpectedStatus(event.status)

        if datetime.datetime.now(datetime.UTC) >= ensure_utc(
            event.registration_deadline
        ):
            raise RegistrationClosed(event.id)

        provider_ticket_id = await self._client.register(
            event_id=event.id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
        )

        ticket = Ticket(
            id=str(uuid.uuid4()),
            provider_ticket_id=provider_ticket_id,
            event_id=event.id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
        )
        await self._tickets.create(ticket)
        await self._events.increment_visitors(event.id, delta=1)
        return ticket
