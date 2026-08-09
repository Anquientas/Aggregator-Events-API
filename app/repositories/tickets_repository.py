from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models
from app.domain.entities import Ticket
from app.exceptions.ticket import DuplicateIdempotencyKey


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
        idempotency_key=row.idempotency_key
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
            idempotency_key=ticket.idempotency_key
        )
        self._session.add(row)

        if ticket.idempotency_key is None:
            return

        try:
            async with self._session.begin_nested():
                await self._session.flush()
        except IntegrityError as exception:
            raise DuplicateIdempotencyKey(
                ticket.idempotency_key
            ) from exception


    async def get(self, ticket_id: str) -> Ticket | None:
        row = await self._session.get(models.Ticket, ticket_id)
        return _to_domain(row) if row else None

    async def mark_cancelled(self, ticket_id: str) -> None:
        row = await self._session.get(models.Ticket, ticket_id)
        if row is not None:
            row.cancelled = True

    async def get_by_idempotency_key(
        self,
        idempotency_key: str
    ) -> Ticket | None:
        statement = select(models.Ticket).where(
            models.Ticket.idempotency_key == idempotency_key
        )
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return _to_domain(row) if row else None
