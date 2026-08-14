import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import models
from app.domain.entities import Event, Place


def _to_domain(row: models.Event) -> Event:
    place = row.place
    return Event(
        id=row.id,
        name=row.name,
        place=Place(
            id=place.id,
            name=place.name,
            city=place.city,
            address=place.address,
            seats_pattern=place.seats_pattern,
        ),
        event_time=row.event_time,
        registration_deadline=row.registration_deadline,
        status=row.status,
        number_of_visitors=row.number_of_visitors,
        changed_at=row.changed_at,
    )


class SqlAlchemyEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, event: Event) -> None:
        stmt = insert(models.Event).values(
            id=event.id,
            name=event.name,
            place_id=event.place.id,
            event_time=event.event_time,
            registration_deadline=event.registration_deadline,
            status=event.status,
            number_of_visitors=event.number_of_visitors,
            changed_at=event.changed_at,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[models.Event.id],
            set_={
                "name": stmt.excluded.name,
                "place_id": stmt.excluded.place_id,
                "event_time": stmt.excluded.event_time,
                "registration_deadline": stmt.excluded.registration_deadline,
                "status": stmt.excluded.status,
                "number_of_visitors": stmt.excluded.number_of_visitors,
                "changed_at": stmt.excluded.changed_at,
            },
        )
        await self._session.execute(stmt)

    async def get(self, event_id: str) -> Event | None:
        stmt = (
            select(models.Event)
            .options(joinedload(models.Event.place))
            .where(models.Event.id == event_id)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def list(
        self,
        date_from: datetime.date | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Event], int]:
        base_stmt = select(models.Event).options(joinedload(
            models.Event.place
        ))
        count_stmt = select(func.count()).select_from(models.Event)

        if date_from is not None:
            base_stmt = base_stmt.where(models.Event.event_time >= date_from)
            count_stmt = count_stmt.where(
                models.Event.event_time >= date_from
            )

        total = (await self._session.execute(count_stmt)).scalar_one()

        base_stmt = (
            base_stmt.order_by(models.Event.event_time)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self._session.execute(base_stmt)).scalars().all()
        return [_to_domain(row) for row in rows], total

    async def increment_visitors(self, event_id: str, delta: int) -> None:
        event = await self._session.get(models.Event, event_id)
        if event is not None:
            event.number_of_visitors = max(
                0,
                event.number_of_visitors + delta
            )

    async def count(self) -> int:
        statement = select(func.count()).select_from(models.Event)
        return (await self._session.execute(statement)).scalar_one()
