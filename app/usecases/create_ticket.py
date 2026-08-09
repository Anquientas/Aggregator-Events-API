import datetime
import uuid

from app.constants.event import EventStatus
from app.constants.outbox import OutboxTypes
from app.constants.ticket import TicketNotificationMessage
from app.core.provider_client import EventsProviderClient
from app.core.timeutils import ensure_utc
from app.domain.entities import OutboxRecord, Ticket
from app.exceptions.event import (
    EventNotFound,
    EventUnexpectedStatus,
    RegistrationClosed,
)
from app.exceptions.ticket import (
    DuplicateIdempotencyKey,
    IdempotencyKeyConflict,
)
from app.repositories.protocols import (
    EventRepository,
    OutboxRepository,
    TicketRepository,
)


class CreateTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        events: EventRepository,
        tickets: TicketRepository,
        outbox: OutboxRepository,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets
        self._outbox = outbox

    async def do(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
        idempotency_key: str | None = None,
    ) -> Ticket:
        if idempotency_key:
            existing = await self._tickets.get_by_idempotency_key(
                idempotency_key
            )
            if existing is not None:
                _ensure_same_request(
                    ticket=existing,
                    event_id=event_id,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    seat=seat
                )
                return existing

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
            idempotency_key=idempotency_key,
        )
        try:
            await self._tickets.create(ticket)
        except DuplicateIdempotencyKey:
            winner = await self._tickets.get_by_idempotency_key(
                idempotency_key
            )
            if winner is None:
                raise
            _ensure_same_request(
                ticket=winner,
                event_id=event_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                seat=seat
            )
            return winner

        outbox_id = str(uuid.uuid4())
        message = TicketNotificationMessage.registration.format(
            event_name=event.name,
            event_time=f'{event.event_time:%d.%m.%Y %H:%M}',
            seat=seat
        )
        await self._outbox.enqueue(
            record=OutboxRecord(
                id=outbox_id,
                event_type=OutboxTypes.notification,
                payload={
                    "message": message,
                    "reference_id": ticket.id,
                    "idempotency_key": outbox_id,
                },
            )
        )

        await self._events.increment_visitors(event.id, delta=1)
        return ticket


def _ensure_same_request(
    ticket: Ticket,
    event_id: str,
    first_name: str,
    last_name: str,
    email: str,
    seat: str,
) -> None:
    if (
        ticket.event_id,
        ticket.first_name,
        ticket.last_name,
        ticket.email,
        ticket.seat,
    ) != (event_id, first_name, last_name, email, seat):
        raise IdempotencyKeyConflict(ticket.idempotency_key)