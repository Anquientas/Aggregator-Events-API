import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.bootstrap.enums import LifespanLogMessage
from app.core.cache import TTLCache
from app.core.provider_client import EventsProviderClient
from app.settings.config import settings
from app.workers.scheduler import BackgroundSyncWorker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(LifespanLogMessage.startup_begin)

    app.state.provider_client = EventsProviderClient(
        base_url=settings.EVENTS_PROVIDER_BASE_URL,
        api_key=settings.EVENTS_PROVIDER_API_KEY,
        timeout=settings.EVENTS_PROVIDER_TIMEOUT,
    )
    app.state.seats_cache = TTLCache(timeout=settings.SEATS_CACHE_TIMEOUT)

    worker = BackgroundSyncWorker(
        client=app.state.provider_client,
        interval=settings.WORKER_SYNC_INTERVAL,
    )
    app.state.sync_worker = worker
    worker.start()

    try:
        yield
    finally:
        logger.info(LifespanLogMessage.shutdown_begin)
        await worker.stop()
        await app.state.provider_client.aclose()
