from app.core.cache import TTLCache
from app.core.exceptions import EventNotFound, EventUnexpectedStatus
from app.core.provider_client import EventsProviderClient
from app.repositories.protocols import EventRepository
from app.usecases.enums import EventStatus


class GetSeatsUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        events: EventRepository,
        cache: TTLCache[list[str]],
    ) -> None:
        self._client = client
        self._events = events
        self._cache = cache

    async def do(self, event_id: str) -> list[str]:
        cached = self._cache.get(event_id)
        if cached is not None:
            return cached

        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFound(event_id)
        if event.status != EventStatus.published:
            raise EventUnexpectedStatus(event.status)

        seats = await self._client.seats(event_id)
        self._cache.set(event_id, seats)
        return seats
