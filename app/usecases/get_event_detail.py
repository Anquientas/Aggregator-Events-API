from app.core.exceptions import EventNotFound
from app.domain.entities import Event
from app.repositories.protocols import EventRepository


class GetEventDetailUsecase:
    def __init__(self, events: EventRepository) -> None:
        self._events = events

    async def do(self, event_id: str) -> Event:
        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFound(event_id)
        return event
