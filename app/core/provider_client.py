import asyncio
import datetime
import logging
from typing import Any, TypedDict

import httpx

from app.constants.provider import ProviderLogMessage
from app.exceptions.provider import EventsProviderError
from app.exceptions.ticket import SeatNotAvailable

logger = logging.getLogger(__name__)

# Сколько раз повторяется запрос при 429 Too Many Requests
_MAX_RATE_LIMIT_RETRIES = 3


class EventsPage(TypedDict):
    next: str | None
    previous: str | None
    results: list[dict[str, Any]]


class EventsProviderClient:
    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        timeout: float = 10.0
    ) -> None:
        self._base_url = base_url.rstrip("/")
        headers = {"x-api-key": api_key} if api_key else {}
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "EventsProviderClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def events(
        self,
        changed_at: datetime.date | None = None,
        next_url: str | None = None,
    ) -> EventsPage:
        if next_url:
            response = await self._request("GET", next_url)
            return response

        params: dict[str, str] = {}
        if changed_at is not None:
            params["changed_at"] = changed_at.strftime("%Y-%m-%d")

        response = await self._request("GET", "/api/events/", params=params)
        return response

    async def seats(self, event_id: str) -> list[str]:
        response = await self._request(
            "GET", f"/api/events/{event_id}/seats/"
        )
        return response["seats"]

    async def register(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str:
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "seat": seat,
        }
        try:
            response = await self._request(
                "POST", f"/api/events/{event_id}/register/", json=payload
            )
        except EventsProviderError as exception:
            if exception.status_code == 400:
                raise SeatNotAvailable(seat) from exception
            raise
        return response["ticket_id"]

    async def cancel(self, event_id: str, ticket_id: str) -> bool:
        payload = {"ticket_id": ticket_id}
        response = await self._request(
            "DELETE", f"/api/events/{event_id}/unregister/", json=payload
        )
        return bool(response.get("success", True))

    async def _request(
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        attempt = 0
        while True:
            try:
                response = await self._http.request(
                    method,
                    url,
                    params=params,
                    json=json
                )
            except httpx.HTTPError as exception:
                raise EventsProviderError(
                    ProviderLogMessage.connection_error.format(
                        error=exception
                    )
                ) from exception

            if (
                response.status_code == 429
                and attempt < _MAX_RATE_LIMIT_RETRIES
            ):
                retry_after = float(response.headers.get("Retry-After", "1"))
                logger.warning(
                    ProviderLogMessage.rate_limited_retry.format(
                        method=method, url=url, interval=retry_after
                    )
                )
                await asyncio.sleep(retry_after)
                attempt += 1
                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exception:
                raise EventsProviderError(
                    ProviderLogMessage.http_error.format(
                        status_code=exception.response.status_code,
                        method=method,
                        url=url,
                        body=exception.response.text[:500],
                    ),
                    status_code=exception.response.status_code,
                ) from exception

            if not response.content:
                return {}

            try:
                return response.json()
            except ValueError as exception:
                raise EventsProviderError(
                    ProviderLogMessage.non_json_response.format(
                        method=method, url=url, body=response.text[:500]
                    )
                ) from exception
