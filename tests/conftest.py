from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

import app.main as main_module
from app.core.cache import TTLCache
from app.core.provider_client import EventsProviderClient
from app.database.engine import Base, get_session


class FakeBackgroundWorker:
    """Заглушка воркера для тестов — не запускает настоящий asyncio-цикл."""

    async def trigger(self) -> None:
        pass

    async def stop(self) -> None:
        pass


@pytest_asyncio.fixture
async def test_engine():
    """Изолированный SQLite-движок в памяти процесса, свой на каждый тест."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
def session_factory(test_engine):
    return async_sessionmaker(
        test_engine,
        expire_on_commit=False,
        class_=AsyncSession
    )


@pytest_asyncio.fixture
def fake_provider_client() -> AsyncMock:
    client = AsyncMock(spec=EventsProviderClient)
    client.events.return_value = {
        "next": None,
        "previous": None,
        "results": []
    }
    return client


@pytest_asyncio.fixture
async def api_client(
    session_factory: async_sessionmaker[AsyncSession],
    fake_provider_client: AsyncMock,
) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @asynccontextmanager
    async def fake_lifespan(app) -> AsyncIterator[None]:
        app.state.provider_client = fake_provider_client
        app.state.seats_cache = TTLCache(timeout=30)
        app.state.sync_worker = FakeBackgroundWorker()
        yield

    main_module.app.dependency_overrides[get_session] = override_get_session
    main_module.app.router.lifespan_context = fake_lifespan

    transport = ASGITransport(app=main_module.app)
    try:
        async with (
            AsyncClient(
                transport=transport,
                base_url="http://test"
            ) as client,
            main_module.app.router.lifespan_context(main_module.app),
        ):
            yield client
    finally:
        main_module.app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture
def sync_repositories(session_factory: async_sessionmaker[AsyncSession]):
    """Фабрика репозиториев на новой сессии —
    для прогона use case синхронизации
    напрямую в тесте (без реального фонового воркера).
    """
    from app.repositories.events_repository import SqlAlchemyEventRepository
    from app.repositories.places_repository import SqlAlchemyPlaceRepository
    from app.repositories.sync_repository import SqlAlchemySyncRepository

    @asynccontextmanager
    async def _make():
        async with session_factory() as session:
            yield (
                SqlAlchemyPlaceRepository(session),
                SqlAlchemyEventRepository(session),
                SqlAlchemySyncRepository(session),
            )
            await session.commit()

    return _make
