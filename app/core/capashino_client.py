import httpx

from app.constants.capashino import CapashinoErrorMessages
from app.exceptions.capashino import CapashinoError, CapashinoTemporaryError


class CapashinoClient:
    def __init__(
        self, base_url: str,
        api_key: str,
        timeout: float = 10.0
    ) -> None:
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip('/'),
            headers={"X-API-Key": api_key},
            timeout=timeout,
        )

    async def send_notification(self, payload: dict) -> bool:
        try:
            response = await self._http.post(
                '/api/notifications',
                json=payload
            )
        except httpx.HTTPError as exception:
            raise CapashinoTemporaryError(
                message=CapashinoErrorMessages.network_error.format(
                    exception=exception
                )
            ) from exception

        if response.status_code in (201, 409):
            return True

        if response.status_code in (400, 401, 422):
            raise CapashinoError(
                message=CapashinoErrorMessages.reject.format(
                    status_code=response.status_code
                ),
                status_code=response.status_code
            )

        raise CapashinoTemporaryError(
            message=CapashinoErrorMessages.unavailable.format(
                status_code=response.status_code
            ),
            status_code=response.status_code
        )
