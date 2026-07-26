import datetime
import logging

from app.core.paginator import EventsPaginator
from app.core.provider_client import EventsProviderClient
from app.domain.entities import Event, Place, SyncState
from app.repositories.protocols import (
    EventRepository,
    PlaceRepository,
    SyncCheckpoint,
    SyncRepository,
)
from app.usecases.enums import SyncLogMessage, SyncStatus

logger = logging.getLogger(__name__)

EPOCH_DATE = datetime.date(2000, 1, 1)
EPOCH_DATETIME = datetime.datetime(2000, 1, 1, tzinfo=datetime.UTC)


class SyncEventsUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        places: PlaceRepository,
        events: EventRepository,
        sync_state: SyncRepository,
        checkpoint: SyncCheckpoint,
    ) -> None:
        self._client = client
        self._places = places
        self._events = events
        self._sync_state = sync_state
        self._checkpoint = checkpoint

    async def do(self) -> SyncState:
        state = await self._sync_state.get_state()
        last_changed_at = state.last_changed_at or EPOCH_DATETIME
        if state.last_changed_at:
            query_date = last_changed_at.date()
        else:
            query_date = EPOCH_DATE

        started_at = datetime.datetime.now(datetime.UTC)
        await self._sync_state.save_state(
            SyncState(
                last_sync_time=state.last_sync_time,
                last_changed_at=state.last_changed_at,
                sync_status=SyncStatus.running,
                last_error=None,
            )
        )
        logger.info(
            SyncLogMessage.started.format(change_at=query_date.isoformat())
        )

        max_changed_at = last_changed_at
        number = 0
        skipped = 0
        try:
            async for raw_event in EventsPaginator(
                self._client, changed_at=query_date
            ):
                try:
                    async with self._checkpoint.savepoint():
                        event = _parse_event(raw_event)
                        await self._places.upsert(event.place)
                        await self._events.upsert(event)
                except Exception:
                    skipped += 1
                    logger.warning(
                        SyncLogMessage.event_skipped.format(
                            event_id=raw_event.get("id", "?")
                        ),
                        exc_info=True,
                    )
                    continue

                if event.changed_at > max_changed_at:
                    max_changed_at = event.changed_at
                number += 1
        except Exception as exception:
            # Сюда попадают уже не проблемы с отдельной записью, а сбои
            # уровня всего запуска — например, обрыв соединения с Events
            # Provider API прямо во время постраничного обхода.
            logger.exception(SyncLogMessage.failed)
            failed_state = SyncState(
                last_sync_time=state.last_sync_time,
                last_changed_at=state.last_changed_at,
                sync_status=SyncStatus.failed,
                last_error=str(exception),
            )
            await self._sync_state.save_state(failed_state)
            return failed_state

        last_error = (
            f"Пропущено событий из-за ошибок: {skipped}" if skipped else None
        )
        final_state = SyncState(
            last_sync_time=started_at,
            last_changed_at=max_changed_at,
            sync_status=SyncStatus.success,
            last_error=last_error,
        )
        await self._sync_state.save_state(final_state)
        logger.info(SyncLogMessage.finished_ok.format(number=number))
        return final_state


def _parse_event(raw: dict) -> Event:
    place_raw = raw["place"]
    place = Place(
        id=place_raw["id"],
        name=place_raw["name"],
        city=place_raw["city"],
        address=place_raw["address"],
        seats_pattern=place_raw.get("seats_pattern"),
    )
    return Event(
        id=raw["id"],
        name=raw["name"],
        place=place,
        event_time=datetime.datetime.fromisoformat(raw["event_time"]),
        registration_deadline=datetime.datetime.fromisoformat(
            raw["registration_deadline"]
        ),
        status=raw["status"],
        number_of_visitors=raw.get("number_of_visitors", 0),
        changed_at=datetime.datetime.fromisoformat(raw["changed_at"]),
    )
