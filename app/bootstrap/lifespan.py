import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.constants.lifespan import LifespanLogMessage
from app.core.cache import TTLCache
from app.core.capashino_client import CapashinoClient
from app.core.provider_client import EventsProviderClient
from app.settings.config import settings
from app.workers.outbox_dispatcher import OutboxDispatcher
from app.workers.scheduler import BackgroundSyncWorker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(LifespanLogMessage.startup_begin)

    app.state.provider_client = EventsProviderClient(
        base_url=settings.provider.base_url,
        api_key=settings.provider.api_key,
        timeout=settings.provider.timeout
    )
    app.state.seats_cache = TTLCache(timeout=settings.SEATS_CACHE_TIMEOUT)

    worker = BackgroundSyncWorker(
        client=app.state.provider_client,
        interval=settings.WORKER_SYNC_INTERVAL,
    )
    app.state.sync_worker = worker
    worker.start()

    outbox_dispatcher = OutboxDispatcher(
        client=CapashinoClient(
            base_url=settings.capashino.base_url,
            api_key=settings.capashino.api_key,
        ),
        interval=settings.OUTBOX_DISPATCH_INTERVAL,
        max_attempts=settings.OUTBOX_MAX_ATTEMPTS,
    )
    app.state.outbox_dispatcher = outbox_dispatcher
    outbox_dispatcher.start()

    try:
        yield
    finally:
        logger.info(LifespanLogMessage.shutdown_begin)
        await worker.stop()
        await app.state.provider_client.aclose()
        await outbox_dispatcher.stop()
