import time

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

from app.core.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path == '/metrics':
            return await call_next(request)

        start_time = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start_time

        endpoint = _resolve_endpoint(request)

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

        return response


def _resolve_endpoint(request: Request) -> str:
    route = request.scope.get('route')
    if route is not None:
        return route.path
    return request.url.path
