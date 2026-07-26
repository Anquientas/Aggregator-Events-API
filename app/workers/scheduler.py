import asyncio
import contextlib
import logging

from app.core.provider_client import EventsProviderClient
from app.database.engine import session_scope
from app.repositories.events_repository import SqlAlchemyEventRepository
from app.repositories.places_repository import SqlAlchemyPlaceRepository
from app.repositories.sync_checkpoint import SqlAlchemySyncCheckpoint
from app.repositories.sync_repository import SqlAlchemySyncRepository
from app.usecases.sync_events import SyncEventsUsecase
from app.workers.enums import WorkerLogMessage

logger = logging.getLogger(__name__)


class BackgroundSyncWorker:
    def __init__(self, client: EventsProviderClient, interval: int) -> None:
        self._client = client
        self._interval = interval
        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(
            self._loop(), name="events-sync-worker"
        )
        logger.info(
            WorkerLogMessage.worker_started.format(interval=self._interval)
        )

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def trigger(self) -> None:
        await self._run_once()

    async def _loop(self) -> None:
        while True:
            await self._run_once()
            await asyncio.sleep(self._interval)

    async def _run_once(self) -> None:
        if self._lock.locked():
            logger.info(WorkerLogMessage.sync_already_running)
            return

        async with self._lock:
            try:
                async with session_scope() as session:
                    usecase = SyncEventsUsecase(
                        client=self._client,
                        places=SqlAlchemyPlaceRepository(session),
                        events=SqlAlchemyEventRepository(session),
                        sync_state=SqlAlchemySyncRepository(session),
                        checkpoint=SqlAlchemySyncCheckpoint(session),
                    )
                    await usecase.do()
            except Exception:
                logger.exception(WorkerLogMessage.unexpected_worker_error)
