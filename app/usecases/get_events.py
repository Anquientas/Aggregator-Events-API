import datetime

from app.domain.entities import Event
from app.repositories.protocols import EventRepository


class GetEventsUsecase:
    def __init__(self, events: EventRepository) -> None:
        self._events = events

    async def do(
        self,
        date_from: datetime.date | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Event], int]:
        return await self._events.list(
            date_from=date_from,
            page=page,
            page_size=page_size
        )
