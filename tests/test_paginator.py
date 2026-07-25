import datetime
from unittest.mock import AsyncMock

import pytest

from app.core.paginator import EventsPaginator
from app.core.provider_client import EventsProviderClient


@pytest.fixture
def client() -> EventsProviderClient:
    return AsyncMock(spec=EventsProviderClient)


async def test_paginator_yields_all_events_across_pages(
    client: AsyncMock
) -> None:
    page1 = {
        "next": "http://provider.test/api/events/?changed_at=2000-01-01&cursor=abc",
        "previous": None,
        "results": [{"id": "e1"}, {"id": "e2"}],
    }
    page2 = {
        "next": None,
        "previous": "http://provider.test/api/events/?changed_at=2000-01-01",
        "results": [{"id": "e3"}],
    }
    client.events.side_effect = [page1, page2]

    events = [event async for event in EventsPaginator(client)]

    assert [e["id"] for e in events] == ["e1", "e2", "e3"]
    assert client.events.call_count == 2


async def test_paginator_passes_changed_at_only_on_first_call(
    client: AsyncMock
) -> None:
    changed_at = datetime.date(2026, 1, 1)
    next_url = "http://provider.test/api/events/?changed_at=2026-01-01&cursor=abc"
    page1 = {"next": next_url, "previous": None, "results": [{"id": "e1"}]}
    page2 = {"next": None, "previous": None, "results": []}
    client.events.side_effect = [page1, page2]

    async for _ in EventsPaginator(client, changed_at=changed_at):
        pass

    first_call = client.events.call_args_list[0]
    second_call = client.events.call_args_list[1]
    assert first_call.kwargs["changed_at"] == changed_at
    assert first_call.kwargs["next_url"] is None
    assert second_call.kwargs["next_url"] == next_url


async def test_paginator_stops_when_single_empty_page(
    client: AsyncMock
) -> None:
    client.events.side_effect = [
        {
            "next": None,
            "previous": None,
            "results": []
        }
    ]

    events = [event async for event in EventsPaginator(client)]

    assert events == []
    client.events.assert_awaited_once()
