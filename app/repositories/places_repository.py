from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models
from app.domain.entities import Place


def _to_domain(row: models.Place) -> Place:
    return Place(
        id=row.id,
        name=row.name,
        city=row.city,
        address=row.address,
        seats_pattern=row.seats_pattern,
    )


class SqlAlchemyPlaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, place: Place) -> None:
        stmt = insert(models.Place).values(
            id=place.id,
            name=place.name,
            city=place.city,
            address=place.address,
            seats_pattern=place.seats_pattern,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[models.Place.id],
            set_={
                "name": stmt.excluded.name,
                "city": stmt.excluded.city,
                "address": stmt.excluded.address,
                "seats_pattern": stmt.excluded.seats_pattern,
            },
        )
        await self._session.execute(stmt)

    async def get(self, place_id: str) -> Place | None:
        row = await self._session.get(models.Place, place_id)
        return _to_domain(row) if row else None
