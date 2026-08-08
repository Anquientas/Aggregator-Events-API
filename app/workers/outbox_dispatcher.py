import asyncio
import contextlib

from app.core.capashino_client import CapashinoClient
from app.database.engine import session_scope
from app.exceptions.capashino import CapashinoError, CapashinoTemporaryError
from app.repositories.outbox_repository import SqlAlchemyOutboxRepository
from app.settings.config import settings


class OutboxDispatcher:
    def __init__(
        self,
        client: CapashinoClient,
        interval: int,
        max_attempts: int
    ) -> None:
        self._client = client
        self._interval = interval
        self._max_attempts = max_attempts
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(
            self._loop(),
            name='outbox-dispatcher'
        )

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _loop(self) -> None:
        while True:
            await self._run_once()
            await asyncio.sleep(self._interval)

    async def _run_once(self) -> None:
        async with session_scope() as session:
            outbox = SqlAlchemyOutboxRepository(session)
            for record in await outbox.get_pending(
                limit=settings.OUTBOX_LIMIT_ROWS
            ):
                if record.attempts >= self._max_attempts:
                    continue
                try:
                    await self._client.send_notification(record.payload)
                except CapashinoTemporaryError as exception:
                    await outbox.mark_failed(
                        record_id=record.id,
                        error=str(exception)
                    )
                except CapashinoError as exception:
                    await outbox.mark_permanently_failed(
                        record_id=record.id,
                        error=str(exception)
                    )
                else:
                    await outbox.mark_sent(record.id)
