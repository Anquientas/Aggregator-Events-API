# Events Aggregator

Сервис-агрегатор мероприятий: синхронизация событий с внешним Events Provider API,
локальное хранение в PostgreSQL, регистрация на мероприятия и надежная (через
Transactional Outbox) отправка уведомлений о покупке билета в Capashino.

## Возможности

- Фоновая инкрементальная синхронизация событий с Events Provider API
- REST API: список, детали событий, свободные места (с локальным кэшем),
  регистрация и отмена регистрации на мероприятие
- **Идемпотентная регистрация** — защита от дублей *билета* при повторной
  отправке запроса клиентом, двойной клик (retry) (см.
  [`docs/idempotency.md`](docs/idempotency.md))
- **Transactional Outbox** — гарантированная доставка *уведомления* об уже
  созданном билете в Capashino: не теряется ни при падении процесса, ни
  при временной недоступности Capashino. Это отдельный от идемпотентности
  регистрации механизм — билет и факт «нужно уведомить» пишутся в одной
  транзакции БД, а сама отправка осуществляется асинхронно и независимо, со своей
  внутренней идемпотентностью на случай повторной попытки доставки
- Мониторинг ошибок через GlitchTip (Sentry SDK)

## Стек

Python 3.13, FastAPI, SQLAlchemy 2.0 (async) + asyncpg, PostgreSQL, Alembic,
httpx, `uv`, `ruff`, `pytest`.

## Архитектура

* app/

  * main.py — сборка FastAPI-приложения (единственный
"рабочий" файл верхнего уровня)
  * settings/config.py — все настройки (pydantic-settings), сгруппированы
по назначению (database/provider/capashino)
  * database/
    * engine.py — engine, сессии, unit-of-work (get_session)
    * models.py — SQLAlchemy ORM-модели
  * domain/entities.py — доменные сущности, не знают о БД или фреймворке
  * schemas/api.py — Pydantic-схемы запросов и ответов API
  * bootstrap/
    * lifespan.py — инициализация ресурсов и фоновых воркеров
при старте приложения
    * glitchtip.py — инициализация GlitchTip
  * core/
    * provider_client.py — весь HTTP-код интеграции с Events Provider
    * capashino_client.py — весь HTTP-код интеграции с Capashino
    * paginator.py — обход cursor-пагинации Events Provider
    * cache.py — локальный (без Redis) TTL-кэш
    * timeutils.py — безопасное сравнение aware/naive дат
  * repositories/ — Repository поверх SQLAlchemy и
протоколы (интерфейсы для usecase'ов)
  * usecases/ — бизнес-логика, не знает о FastAPI/ORM
  * workers/
    * scheduler.py — фоновая синхронизация событий
    * outbox_dispatcher.py — фоновая отправка уведомлений из outbox
  * api/ — тонкие FastAPI-роутеры и DI
  * constants/ — тексты сообщений и статусы (Enum),
сгруппированы по сущностям
  * exceptions/ — доменные исключения, сгруппированы по сущностям

alembic/ — миграции схемы БД (накатываются, никогда не пересоздаются)
tests/ — unit- и интеграционные тесты
docs/ — дополнительная документация (идемпотентность и т.п.)

Принцип: `usecases` ничего не знают про SQLAlchemy/FastAPI и работают только
через протоколы репозиториев; `repositories/*_repository.py` — единственное
место, где ORM-модель превращается в доменный объект и обратно; `api/*.py` —
только валидация запроса и перевод исключения usecase'а в HTTP-ответ.

## Быстрый старт

### Через docker-compose

```bash
cp .env.example .env   # заполнить реальными значениями
docker compose up --build
```

Приложение — `http://localhost:8000`, документация API — `http://localhost:8000/docs`.
Миграции применяются автоматически при старте контейнера.

### Локально с `uv`

```bash
uv sync --group dev
cp .env.example .env
docker compose up database -d      # только БД
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Переменные окружения

| Переменная | Обязательна | Назначение |
|---|---|---|
| `POSTGRES_DATABASE_NAME`, `POSTGRES_USERNAME`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` | Да | Подключение к БД |
| `EVENTS_PROVIDER_BASE_URL`, `EVENTS_PROVIDER_API_KEY` | Нет (пусто по умолчанию) | Интеграция с Events Provider API |
| `WORKER_SYNC_INTERVAL` | Нет (по умолчанию сутки) | Интервал фоновой синхронизации событий, с |
| `SEATS_CACHE_TIMEOUT` | Нет (по умолчанию 30) | TTL локального кэша свободных мест, с |
| `DEFAULT_PAGE_SIZE` | Нет (по умолчанию 20) | Размер страницы `GET /api/events` |
| `CAPASHINO_BASE_URL`, `CAPASHINO_API_KEY` | Нет | Интеграция с Capashino (уведомления) |
| `OUTBOX_DISPATCH_INTERVAL`, `OUTBOX_MAX_ATTEMPTS`, `OUTBOX_LIMIT_ROWS` | Нет | Параметры фонового воркера outbox |
| `SENTRY_DSN` | Нет | Подключение к GlitchTip; если не задано — интеграция не включается |

Полный пример — в [`.env.example`](.env.example).

## API

Полная актуальная схема — в `/docs` (Swagger) и `/redoc`.
Основные эндпоинты:

| Метод и путь | Назначение |
|---|---|
| `GET /api/health` | Проверка развертывания |
| `POST /api/sync/trigger` | Ручной запуск синхронизации событий |
| `GET /api/events` | Список событий (пагинация, фильтр по дате) |
| `GET /api/events/{event_id}` | Детали события |
| `GET /api/events/{event_id}/seats` | Свободные места (кэш 30 с) |
| `POST /api/tickets` | Регистрация на мероприятие (см. идемпотентность ниже) |
| `DELETE /api/tickets/{ticket_id}` | Отмена регистрации |

> **!!!** `GET /api/glitchtip/trigger-error` Использовался для разовой проверки доставки ошибок в GlitchTip после
> подключения интеграции. Перед релизом рекомендуется либо убрать его
> совсем, либо закрыть авторизацией или фичефлагом.

Идемпотентность `POST /api/tickets` (ключ, коды 409, поведение при повторах) —
подробно в [`docs/idempotency.md`](docs/idempotency.md).

## Фоновые процессы

Два фоновых процесса запускаются в `app/bootstrap/lifespan.py` как обычные корутины в том же
процессе (`asyncio.create_task`), без отдельного воркера или очереди:

- **`BackgroundSyncWorker`** (`workers/scheduler.py`) — раз в `WORKER_SYNC_INTERVAL`
  инкрементально подтягивает события с Events Provider API. Одна битая запись
  от провайдера не откатывает весь прогон — каждое событие изолировано своим
  `SAVEPOINT`.
- **`OutboxDispatcher`** (`workers/outbox_dispatcher.py`) — раз в
  `OUTBOX_DISPATCH_INTERVAL` вычитывает неотправленные записи из таблицы
  `outbox` и отправляет их в Capashino. Каждая запись тоже изолирована своим
  `SAVEPOINT` — сбой одного уведомления не откатывает уже успешно
  отправленные соседние записи из той же пачки.

## Transactional Outbox

Запись о том, что нужно уведомить пользователя, сохраняется **в той же
транзакции БД**, что и сам билет (`CreateTicketUsecase`, `tickets` и
`outbox` одним `commit`). Поэтому событие «билет куплен» не может потеряться:
либо сохраняется билет и запись на отправку вместе, либо не сохраняется
ничего. Сама отправка — уже отдельный, асинхронный шаг (`OutboxDispatcher`),
не блокирующий ответ пользователю.

## Тесты

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

Тесты не требуют поднятого PostgreSQL — каждый тест получает изолированный
SQLite-движок в памяти процесса (`tests/conftest.py`), что позволяет
безопасно использовать их параллельно.

## Миграции

```bash
uv run alembic upgrade head
```

Схема **накатывается** новыми ревизиями поверх уже примененных.

## CI/CD

Последовательность CI/CD следующая: `.github/workflows/workflow.yml`: `lint` (ruff), `test` (pytest и проверка,
что миграции применяются), `build-and-push` (образ), `deploy`.
Деплой выполняется только после успешного прохождения линтера и тестов.

## Мониторинг ошибок

Все необработанные исключения автоматически уходят в GlitchTip через
`sentry-sdk`, если задан `SENTRY_DSN` (`app/bootstrap/glitchtip.py`). Если
переменная не задана — интеграция просто не включается, приложение работает
как обычно.
