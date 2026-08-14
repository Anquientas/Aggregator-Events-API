from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import events, glitchtip, health, metrics, sync, tickets
from app.bootstrap.glitchtip import setup_glitchtip
from app.bootstrap.lifespan import lifespan
from app.bootstrap.metrics_middleware import MetricsMiddleware

setup_glitchtip()

app = FastAPI(title='Events Aggregator', lifespan=lifespan)
app.add_middleware(MetricsMiddleware)

app.include_router(health.router)
app.include_router(sync.router)
app.include_router(events.router)
app.include_router(tickets.router)
app.include_router(glitchtip.router)
app.include_router(metrics.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exception: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": jsonable_encoder(exception.errors())}
    )
