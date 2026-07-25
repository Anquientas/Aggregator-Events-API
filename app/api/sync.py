import asyncio

from fastapi import APIRouter, Request

from app.schemas.api import SyncTriggerResponse

router = APIRouter(tags=["sync"])


@router.post("/api/sync/trigger", response_model=SyncTriggerResponse)
async def trigger_sync(request: Request) -> SyncTriggerResponse:
    worker = request.app.state.sync_worker
    asyncio.create_task(worker.trigger())
    return SyncTriggerResponse(status="triggered")
