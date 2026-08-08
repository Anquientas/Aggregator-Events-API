from fastapi import APIRouter

from app.constants.glitchtip import GlitchtipHealthMessage

router = APIRouter(tags=['glitchtip'])


@router.get('/api/glitchtip/trigger-error')
async def trigger_error() -> None:
    raise RuntimeError(GlitchtipHealthMessage.runtime_error)
