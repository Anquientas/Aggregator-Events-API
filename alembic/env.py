import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.database.engine import Base
from app.database.models import (  # noqa: F401 — регистрируют модели в Base.metadata
    Event,
    Outbox,
    Place,
    SyncMetadata,
    Ticket
)
from app.settings.config import settings

# Alembic Config object — доступ к значениям из alembic.ini
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные наших моделей — используются для автогенерации миграций
target_metadata = Base.metadata

# URL базы данных берём из настроек приложения (единый источник правды,
# см. app/settings/config.py), а не дублируем его в alembic.ini
config.set_main_option("sqlalchemy.url", settings.database.url)


def run_migrations_offline() -> None:
    """Генерация SQL без подключения к БД (`alembic upgrade head --sql`)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Применение миграций к реальной БД (обычный режим `alembic upgrade head`)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
