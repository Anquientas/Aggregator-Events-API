from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.outbox import OutboxStatus
from app.database import models
from app.domain.entities import OutboxRecord


def _to_domain(row: models.Outbox) -> OutboxRecord:
    return OutboxRecord(
        id=row.id,
        event_type=row.event_type,
        payload=row.payload,
        status=row.status,
        attempts_number=row.attempts_number,
        created_at=row.created_at,
        changed_at=row.changed_at,
        error=row.error
    )


class SqlAlchemyOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enqueue(self, record: OutboxRecord) -> None:
        self._session.add(
            models.Outbox(
                id=record.id,
                event_type=record.event_type,
                payload=record.payload,
                status=OutboxStatus.pending
            )
        )

    async def get_pending(self, limit: int) -> list[OutboxRecord]:
        statement = (
            select(models.Outbox)
            .where(models.Outbox.status == OutboxStatus.pending)
            .order_by(models.Outbox.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        rows = (await self._session.execute(statement)).scalars().all()
        return [_to_domain(row) for row in rows]

    async def mark_sent(self, record_id: str) -> None:
        row = await self._session.get(models.Outbox, record_id)
        if row is not None:
            row.status = OutboxStatus.sent
            row.error = ''

    async def mark_failed(self, record_id: str, error: str) -> None:
        row = await self._session.get(models.Outbox, record_id)
        if row is not None:
            row.attempts_number += 1
            row.error = error[:2000]

    async def mark_permanently_failed(
        self,
        record_id: str,
        error: str
    ) -> None:
        row = await self._session.get(models.Outbox, record_id)
        if row is not None:
            row.status = OutboxStatus.failed
            row.attempts_number += 1
            row.error = error[:2000]
