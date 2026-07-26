from contextlib import AbstractAsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemySyncCheckpoint:
    """SAVEPOINT на событие: см. docstring `SyncCheckpoint` в protocols.py."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def savepoint(self) -> AbstractAsyncContextManager[None]:
        # session.begin_nested() уже является асинхронным контекстным
        # менеджером: при исключении сам делает ROLLBACK TO SAVEPOINT,
        # при успехе — RELEASE SAVEPOINT. Ничего дополнительно не нужно.
        return self._session.begin_nested()
