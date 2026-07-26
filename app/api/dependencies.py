from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import TTLCache
from app.core.provider_client import EventsProviderClient
from app.database.engine import get_session
from app.repositories.events_repository import SqlAlchemyEventRepository
from app.repositories.places_repository import SqlAlchemyPlaceRepository
from app.repositories.sync_checkpoint import SqlAlchemySyncCheckpoint
from app.repositories.sync_repository import SqlAlchemySyncRepository
from app.repositories.tickets_repository import SqlAlchemyTicketRepository
from app.usecases.cancel_ticket import CancelTicketUsecase
from app.usecases.create_ticket import CreateTicketUsecase
from app.usecases.get_event_detail import GetEventDetailUsecase
from app.usecases.get_events import GetEventsUsecase
from app.usecases.get_seats import GetSeatsUsecase
from app.usecases.sync_events import SyncEventsUsecase


def get_provider_client(request: Request) -> EventsProviderClient:
    return request.app.state.provider_client


def get_seats_cache(request: Request) -> TTLCache[list[str]]:
    return request.app.state.seats_cache


async def get_event_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncIterator[SqlAlchemyEventRepository]:
    yield SqlAlchemyEventRepository(session)


async def get_place_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncIterator[SqlAlchemyPlaceRepository]:
    yield SqlAlchemyPlaceRepository(session)


async def get_ticket_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncIterator[SqlAlchemyTicketRepository]:
    yield SqlAlchemyTicketRepository(session)


async def get_sync_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncIterator[SqlAlchemySyncRepository]:
    yield SqlAlchemySyncRepository(session)


async def get_sync_checkpoint(
    session: AsyncSession = Depends(get_session),
) -> AsyncIterator[SqlAlchemySyncCheckpoint]:
    yield SqlAlchemySyncCheckpoint(session)


def get_events_usecase(
    events: SqlAlchemyEventRepository = Depends(get_event_repository),
) -> GetEventsUsecase:
    return GetEventsUsecase(events)


def get_event_detail_usecase(
    events: SqlAlchemyEventRepository = Depends(get_event_repository),
) -> GetEventDetailUsecase:
    return GetEventDetailUsecase(events)


def get_seats_usecase(
    client: EventsProviderClient = Depends(get_provider_client),
    events: SqlAlchemyEventRepository = Depends(get_event_repository),
    cache: TTLCache[list[str]] = Depends(get_seats_cache),
) -> GetSeatsUsecase:
    return GetSeatsUsecase(client, events, cache)


def get_create_ticket_usecase(
    client: EventsProviderClient = Depends(get_provider_client),
    events: SqlAlchemyEventRepository = Depends(get_event_repository),
    tickets: SqlAlchemyTicketRepository = Depends(get_ticket_repository),
) -> CreateTicketUsecase:
    return CreateTicketUsecase(client, events, tickets)


def get_cancel_ticket_usecase(
    client: EventsProviderClient = Depends(get_provider_client),
    events: SqlAlchemyEventRepository = Depends(get_event_repository),
    tickets: SqlAlchemyTicketRepository = Depends(get_ticket_repository),
) -> CancelTicketUsecase:
    return CancelTicketUsecase(client, events, tickets)


def get_sync_usecase(
    client: EventsProviderClient = Depends(get_provider_client),
    places: SqlAlchemyPlaceRepository = Depends(get_place_repository),
    events: SqlAlchemyEventRepository = Depends(get_event_repository),
    sync_state: SqlAlchemySyncRepository = Depends(get_sync_repository),
    checkpoint: SqlAlchemySyncCheckpoint = Depends(get_sync_checkpoint),
) -> SyncEventsUsecase:
    return SyncEventsUsecase(client, places, events, sync_state, checkpoint)
