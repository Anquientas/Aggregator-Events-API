import datetime
from collections.abc import AsyncIterator
from typing import Any

from app.core.provider_client import EventsProviderClient


class EventsPaginator:
    def __init__(
        self,
        client: EventsProviderClient,
        changed_at: datetime.date | None = None,
    ) -> None:
        self._client = client
        self._changed_at = changed_at
        self._next_url: str | None = None
        self._buffer: list[dict[str, Any]] = []
        self._exhausted = False
        self._started = False

    def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        return self

    async def __anext__(self) -> dict[str, Any]:
        while not self._buffer:
            if self._exhausted:
                raise StopAsyncIteration
            await self._fetch_next_page()
        return self._buffer.pop(0)

    async def _fetch_next_page(self) -> None:
        if not self._started:
            self._started = True
            page = await self._client.events(
                changed_at=self._changed_at,
                next_url=None
            )
        else:
            if not self._next_url:
                self._exhausted = True
                return
            page = await self._client.events(next_url=self._next_url)

        self._buffer = list(page["results"])
        self._next_url = page.get("next")
        if not self._next_url:
            self._exhausted = True
