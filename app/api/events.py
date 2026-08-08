import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies import (
    get_event_detail_usecase,
    get_events_usecase,
    get_seats_usecase,
)
from app.constants.ticket import EventErrorDetail
from app.domain.entities import Event
from app.exceptions.event import EventNotFound, EventUnexpectedStatus
from app.schemas.api import (
    EventDetail,
    EventListItem,
    EventListResponse,
    PlaceDetail,
    PlaceShort,
    SeatsResponse,
)
from app.settings.config import settings
from app.usecases.get_event_detail import GetEventDetailUsecase
from app.usecases.get_events import GetEventsUsecase
from app.usecases.get_seats import GetSeatsUsecase

router = APIRouter(prefix="/api/events", tags=["events"])


def _to_list_item(event: Event) -> EventListItem:
    return EventListItem(
        id=event.id,
        name=event.name,
        place=PlaceShort(
            id=event.place.id,
            name=event.place.name,
            city=event.place.city,
            address=event.place.address,
        ),
        event_time=event.event_time,
        registration_deadline=event.registration_deadline,
        status=event.status,
        number_of_visitors=event.number_of_visitors,
    )


def _to_detail(event: Event) -> EventDetail:
    return EventDetail(
        id=event.id,
        name=event.name,
        place=PlaceDetail(
            id=event.place.id,
            name=event.place.name,
            city=event.place.city,
            address=event.place.address,
            seats_pattern=event.place.seats_pattern,
        ),
        event_time=event.event_time,
        registration_deadline=event.registration_deadline,
        status=event.status,
        number_of_visitors=event.number_of_visitors,
    )


def _page_url(request: Request, page: int, page_size: int) -> str:
    url = request.url.include_query_params(page=page, page_size=page_size)
    return str(url)


@router.get("", response_model=EventListResponse)
async def list_events(
    request: Request,
    date_from: datetime.date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=100),
    usecase: GetEventsUsecase = Depends(get_events_usecase),
) -> EventListResponse:
    events, total = await usecase.do(
        date_from=date_from,
        page=page,
        page_size=page_size
    )

    has_next = page * page_size < total
    has_previous = page > 1

    return EventListResponse(
        count=total,
        next=_page_url(
            request,
            page + 1,
            page_size
        ) if has_next else None,
        previous=_page_url(
            request,
            page - 1,
            page_size
        ) if has_previous else None,
        results=[_to_list_item(event) for event in events],
    )


@router.get("/{event_id}", response_model=EventDetail)
async def get_event(
    event_id: str,
    usecase: GetEventDetailUsecase = Depends(get_event_detail_usecase),
) -> EventDetail:
    try:
        event = await usecase.do(event_id)
    except EventNotFound as exception:
        raise HTTPException(
            status_code=404,
            detail=EventErrorDetail.event_not_found
        ) from exception
    return _to_detail(event)


@router.get("/{event_id}/seats", response_model=SeatsResponse)
async def get_event_seats(
    event_id: str,
    usecase: GetSeatsUsecase = Depends(get_seats_usecase),
) -> SeatsResponse:
    try:
        seats = await usecase.do(event_id)
    except EventNotFound as exception:
        raise HTTPException(
            status_code=404,
            detail=EventErrorDetail.event_not_found
        ) from exception
    except EventUnexpectedStatus as exception:
        raise HTTPException(
            status_code=409,
            detail=EventErrorDetail.seats_unavailable_status
        ) from exception
    return SeatsResponse(event_id=event_id, available_seats=seats)
