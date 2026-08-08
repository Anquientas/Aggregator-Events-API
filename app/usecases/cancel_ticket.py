import datetime

from app.core.provider_client import EventsProviderClient
from app.core.timeutils import ensure_utc
from app.exceptions.event import EventAlreadyOccurred
from app.exceptions.ticket import TicketNotFound
from app.repositories.protocols import EventRepository, TicketRepository


class CancelTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        events: EventRepository,
        tickets: TicketRepository,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets

    async def do(self, ticket_id: str) -> bool:
        ticket = await self._tickets.get(ticket_id)
        if not ticket:
            raise TicketNotFound(ticket_id)

        event = await self._events.get(ticket.event_id)
        if event is not None and datetime.datetime.now(
            datetime.UTC
        ) >= ensure_utc(
            event.event_time
        ):
            raise EventAlreadyOccurred(ticket.event_id)

        success = await self._client.cancel(
            ticket.event_id,
            ticket.provider_ticket_id
        )
        if success:
            await self._tickets.mark_cancelled(ticket.id)
            await self._events.increment_visitors(ticket.event_id, delta=-1)
        return success
