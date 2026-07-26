from unittest.mock import AsyncMock

from httpx import AsyncClient

from app.core.exceptions import SeatNotAvailable
from app.usecases.sync_events import SyncEventsUsecase

RAW_EVENT = {
    "id": "event-1",
    "name": "Тестовый концерт",
    "place": {
        "id": "place-1",
        "name": "Дворец спорта",
        "city": "Москва",
        "address": "ул. Ленина, 1",
        "seats_pattern": "A1-100",
    },
    "event_time": "2027-01-11T17:00:00+03:00",
    "registration_deadline": "2027-01-10T17:00:00+03:00",
    "status": "published",
    "number_of_visitors": 5,
    "changed_at": "2026-01-01T00:00:00+00:00",
}


async def _sync_one_event(
    sync_repositories, fake_provider_client: AsyncMock
) -> None:
    fake_provider_client.events.return_value = {
        "next": None,
        "previous": None,
        "results": [RAW_EVENT],
    }
    async with sync_repositories() as (
        places,
        events,
        sync_state,
        checkpoint,
    ):
        usecase = SyncEventsUsecase(
            client=fake_provider_client,
            places=places,
            events=events,
            sync_state=sync_state,
            checkpoint=checkpoint,
        )
        state = await usecase.do()
    assert state.sync_status == "success"


async def test_health_endpoint(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_sync_trigger_endpoint(api_client: AsyncClient) -> None:
    response = await api_client.post("/api/sync/trigger")

    assert response.status_code == 200
    assert response.json() == {"status": "triggered"}


async def test_list_events_after_sync(
    api_client, sync_repositories, fake_provider_client
) -> None:
    await _sync_one_event(sync_repositories, fake_provider_client)

    response = await api_client.get("/api/events")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["id"] == "event-1"
    assert body["results"][0]["place"]["city"] == "Москва"


async def test_get_event_detail(
    api_client, sync_repositories, fake_provider_client
) -> None:
    await _sync_one_event(sync_repositories, fake_provider_client)

    response = await api_client.get("/api/events/event-1")

    assert response.status_code == 200
    body = response.json()
    assert body["place"]["seats_pattern"] == "A1-100"
    assert body["status"] == "published"


async def test_get_event_detail_not_found(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/events/does-not-exist")

    assert response.status_code == 404


async def test_seats_endpoint_uses_local_cache(
    api_client, sync_repositories, fake_provider_client
) -> None:
    await _sync_one_event(sync_repositories, fake_provider_client)
    fake_provider_client.seats.return_value = ["A1", "A2", "A3"]

    first = await api_client.get("/api/events/event-1/seats")
    second = await api_client.get("/api/events/event-1/seats")

    assert first.status_code == second.status_code == 200
    assert first.json()["available_seats"] == ["A1", "A2", "A3"]
    # Второй запрос обслужен из локального (in-memory, без Redis) кэша.
    fake_provider_client.seats.assert_awaited_once_with("event-1")


async def test_create_and_cancel_ticket_flow(
    api_client, sync_repositories, fake_provider_client
) -> None:
    await _sync_one_event(sync_repositories, fake_provider_client)
    fake_provider_client.register.return_value = "provider-ticket-1"
    fake_provider_client.cancel.return_value = True

    create_response = await api_client.post(
        "/api/tickets",
        json={
            "event_id": "event-1",
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": "ivan@example.com",
            "seat": "A15",
        },
    )
    assert create_response.status_code == 201
    ticket_id = create_response.json()["ticket_id"]
    fake_provider_client.register.assert_awaited_once_with(
        event_id="event-1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A15",
    )

    cancel_response = await api_client.delete(f"/api/tickets/{ticket_id}")
    assert cancel_response.status_code == 200
    assert cancel_response.json() == {"success": True}
    fake_provider_client.cancel.assert_awaited_once_with(
        "event-1", "provider-ticket-1"
    )


async def test_create_ticket_seat_already_taken_maps_to_409(
    api_client, sync_repositories, fake_provider_client
) -> None:
    await _sync_one_event(sync_repositories, fake_provider_client)
    fake_provider_client.register.side_effect = SeatNotAvailable("A15")

    response = await api_client.post(
        "/api/tickets",
        json={
            "event_id": "event-1",
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": "ivan@example.com",
            "seat": "A15",
        },
    )

    assert response.status_code == 409


async def test_create_ticket_for_unknown_event_returns_404(
    api_client: AsyncClient,
) -> None:
    response = await api_client.post(
        "/api/tickets",
        json={
            "event_id": "does-not-exist",
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": "ivan@example.com",
            "seat": "A15",
        },
    )

    assert response.status_code == 404


async def test_cancel_unknown_ticket_returns_404(
    api_client: AsyncClient,
) -> None:
    response = await api_client.delete("/api/tickets/does-not-exist")

    assert response.status_code == 404
