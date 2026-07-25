import datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.core.exceptions import EventsProviderError, SeatNotAvailable
from app.core.provider_client import EventsProviderClient


def _make_response(
    json_body: dict | None = None,
    status_code: int = 200,
    text_body: str | None = None,
) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.headers = {}
    if text_body is not None:
        response.content = text_body.encode()
        response.text = text_body
        response.json.side_effect = ValueError("not a JSON body")
    else:
        response.content = b"{}" if json_body is not None else b""
        response.json.return_value = json_body or {}
        response.text = str(json_body)
    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=response
        )
    else:
        response.raise_for_status.side_effect = None
    return response


@pytest.fixture
def client() -> EventsProviderClient:
    return EventsProviderClient(
        base_url="http://provider.test",
        api_key="secret"
    )


def test_client_sends_api_key_header(client: EventsProviderClient) -> None:
    assert client._http.headers["x-api-key"] == "secret"


async def test_events_uses_changed_at_as_date_only(
    client: EventsProviderClient
) -> None:
    page = {"next": None, "previous": None, "results": [{"id": "e1"}]}
    client._http.request = AsyncMock(return_value=_make_response(page))

    result = await client.events(changed_at=datetime.date(2000, 1, 1))

    client._http.request.assert_awaited_once()
    args, kwargs = client._http.request.await_args
    assert args[0] == "GET"
    assert args[1] == "/api/events/"
    assert kwargs["params"] == {"changed_at": "2000-01-01"}
    assert result == page


async def test_events_follows_next_url_directly(
    client: EventsProviderClient
) -> None:
    page = {"next": None, "previous": None, "results": []}
    client._http.request = AsyncMock(return_value=_make_response(page))

    next_url = (
        "http://provider.test/api/events/"
        "?changed_at=2000-01-01&cursor=abc123"
    )
    await client.events(next_url=next_url)

    args, kwargs = client._http.request.await_args
    assert args[0] == "GET"
    assert args[1] == next_url
    assert kwargs["params"] is None


async def test_seats_returns_available_seats_list(
    client: EventsProviderClient
) -> None:
    body = {"seats": ["A1", "A2"]}
    client._http.request = AsyncMock(return_value=_make_response(body))

    seats = await client.seats("e1")

    assert seats == ["A1", "A2"]
    args, _ = client._http.request.await_args
    assert args[1] == "/api/events/e1/seats/"


async def test_register_returns_ticket_id_and_omits_event_id_from_body(
    client: EventsProviderClient,
) -> None:
    body = {"ticket_id": "t-1"}
    client._http.request = AsyncMock(return_value=_make_response(body))

    ticket_id = await client.register(
        event_id="e1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A15"
    )

    assert ticket_id == "t-1"
    args, kwargs = client._http.request.await_args
    assert args[1] == "/api/events/e1/register/"
    assert kwargs["json"] == {
        "first_name": "Иван",
        "last_name": "Иванов",
        "email": "ivan@example.com",
        "seat": "A15",
    }


async def test_register_raises_seat_not_available_on_400(
    client: EventsProviderClient
) -> None:
    client._http.request = AsyncMock(
        return_value=_make_response(
            {"detail": "This ticket is not available (already sold)."},
            status_code=400
        )
    )

    with pytest.raises(SeatNotAvailable):
        await client.register(
            event_id="e1",
            first_name="Иван",
            last_name="Иванов",
            email="ivan@example.com",
            seat="A15",
        )


async def test_cancel_sends_ticket_id_in_body_to_unregister_path(
    client: EventsProviderClient,
) -> None:
    client._http.request = AsyncMock(
        return_value=_make_response({"success": True})
    )

    assert await client.cancel("e1", "t-1") is True

    args, kwargs = client._http.request.await_args
    assert args[0] == "DELETE"
    assert args[1] == "/api/events/e1/unregister/"
    assert kwargs["json"] == {"ticket_id": "t-1"}


async def test_http_error_is_wrapped_in_events_provider_error(
    client: EventsProviderClient
) -> None:
    client._http.request = AsyncMock(
        return_value=_make_response({"detail": "boom"}, status_code=500)
    )

    with pytest.raises(EventsProviderError):
        await client.events()


async def test_html_error_body_is_wrapped_in_events_provider_error(
    client: EventsProviderClient,
) -> None:
    client._http.request = AsyncMock(
        return_value=_make_response(
            text_body=(
                "UnexpectedEventStatus:"
                " Event is not published for registration."
            )
        )
    )

    with pytest.raises(EventsProviderError):
        await client.seats("e1")


async def test_rate_limit_retries_then_succeeds(
    client: EventsProviderClient
) -> None:
    rate_limited = _make_response({"detail": "slow down"}, status_code=429)
    rate_limited.headers = {"Retry-After": "0"}
    ok_response = _make_response({"seats": ["A1"]})
    client._http.request = AsyncMock(side_effect=[rate_limited, ok_response])

    seats = await client.seats("e1")

    assert seats == ["A1"]
    assert client._http.request.await_count == 2
