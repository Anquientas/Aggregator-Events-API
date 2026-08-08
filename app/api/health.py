from fastapi import APIRouter

from app.constants.health import HealthResponseStatus
from app.schemas.api import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status=HealthResponseStatus.ok)
