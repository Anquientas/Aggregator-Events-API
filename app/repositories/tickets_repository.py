from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models
from app.domain.entities import Ticket


def _to_domain(row: models.Ticket) -> Ticket:
    return Ticket(
        id=row.id,
        provider_ticket_id=row.provider_ticket_id,
        event_id=row.event_id,
        first_name=row.first_name,
        last_name=row.last_name,
        email=row.email,
        seat=row.seat,
        cancelled=row.cancelled,
    )


class SqlAlchemyTicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, ticket: Ticket) -> None:
        row = models.Ticket(
            id=ticket.id,
            provider_ticket_id=ticket.provider_ticket_id,
            event_id=ticket.event_id,
            first_name=ticket.first_name,
            last_name=ticket.last_name,
            email=ticket.email,
            seat=ticket.seat,
            cancelled=ticket.cancelled,
        )
        self._session.add(row)

    async def get(self, ticket_id: str) -> Ticket | None:
        row = await self._session.get(models.Ticket, ticket_id)
        return _to_domain(row) if row else None

    async def mark_cancelled(self, ticket_id: str) -> None:
        row = await self._session.get(models.Ticket, ticket_id)
        if row is not None:
            row.cancelled = True
