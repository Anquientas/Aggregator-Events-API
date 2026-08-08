import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.settings.config import settings


def setup_glitchtip() -> None:
    if not settings.GLITCHTIP_DSN:
        return

    sentry_sdk.init(
        dsn=settings.GLITCHTIP_DSN,
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )