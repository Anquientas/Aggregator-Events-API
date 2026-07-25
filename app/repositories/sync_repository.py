from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models
from app.domain.entities import SyncState
from app.repositories.enums import SyncStatus

_STATE_ROW_ID = 1


class SqlAlchemySyncRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_state(self) -> SyncState:
        row = await self._session.get(models.SyncMetadata, _STATE_ROW_ID)
        if row is None:
            return SyncState(
                last_sync_time=None,
                last_changed_at=None,
                sync_status=SyncStatus.idle
            )
        return SyncState(
            last_sync_time=row.last_sync_time,
            last_changed_at=row.last_changed_at,
            sync_status=row.sync_status,
            last_error=row.last_error,
        )

    async def save_state(self, state: SyncState) -> None:
        stmt = insert(models.SyncMetadata).values(
            id=_STATE_ROW_ID,
            last_sync_time=state.last_sync_time,
            last_changed_at=state.last_changed_at,
            sync_status=state.sync_status,
            last_error=state.last_error,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[models.SyncMetadata.id],
            set_={
                "last_sync_time": stmt.excluded.last_sync_time,
                "last_changed_at": stmt.excluded.last_changed_at,
                "sync_status": stmt.excluded.sync_status,
                "last_error": stmt.excluded.last_error,
            },
        )
        await self._session.execute(stmt)
