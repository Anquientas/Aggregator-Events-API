import asyncio

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

from app.core.metrics import (
    EVENTS_TOTAL,
    TICKETS_CANCELLED_TOTAL,
    TICKETS_CREATED_TOTAL,
)
from app.database.engine import session_scope
from app.repositories.events_repository import SqlAlchemyEventRepository
from app.repositories.tickets_repository import SqlAlchemyTicketRepository

router = APIRouter(tags=["metrics"])


async def _count_events() -> int:
    async with session_scope() as session:
        return await SqlAlchemyEventRepository(session).count()


async def _count_tickets() -> int:
    async with session_scope() as session:
        return await SqlAlchemyTicketRepository(session).count()


async def _count_cancelled_tickets() -> int:
    async with session_scope() as session:
        return await SqlAlchemyTicketRepository(session).count_cancelled()


@router.get("/metrics")
async def metrics() -> Response:
    events_count, tickets_count, cancelled_count = await asyncio.gather(
        _count_events(),
        _count_tickets(),
        _count_cancelled_tickets(),
    )
    EVENTS_TOTAL.set(events_count)
    TICKETS_CREATED_TOTAL.set(tickets_count)
    TICKETS_CANCELLED_TOTAL.set(cancelled_count)

    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )
