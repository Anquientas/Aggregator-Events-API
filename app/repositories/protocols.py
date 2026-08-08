import datetime
from contextlib import AbstractAsyncContextManager
from typing import Protocol

from app.domain.entities import Event, OutboxRecord, Place, SyncState, Ticket


class PlaceRepository(Protocol):
    async def upsert(self, place: Place) -> None: ...

    async def get(self, place_id: str) -> Place | None: ...


class EventRepository(Protocol):
    async def upsert(self, event: Event) -> None: ...

    async def get(self, event_id: str) -> Event | None: ...

    async def list(
        self,
        date_from: datetime.date | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Event], int]: ...

    async def increment_visitors(self, event_id: str, delta: int) -> None: ...


class TicketRepository(Protocol):
    async def create(self, ticket: Ticket) -> None: ...

    async def get(self, ticket_id: str) -> Ticket | None: ...

    async def mark_cancelled(self, ticket_id: str) -> None: ...


class SyncRepository(Protocol):
    async def get_state(self) -> SyncState: ...

    async def save_state(self, state: SyncState) -> None: ...


class SyncCheckpoint(Protocol):
    """Изолирует изменения одного события от остальной части синхронизации."""

    def savepoint(self) -> AbstractAsyncContextManager[None]: ...


class OutboxRepository(Protocol):
    async def enqueue(self, record: OutboxRecord) -> None: ...

    async def get_pending(self, limit: int) -> list[OutboxRecord]: ...

    async def mark_sent(self, record_id: str) -> None: ...

    async def mark_failed(self, record_id: str, error: str) -> None: ...
