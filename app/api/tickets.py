from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_cancel_ticket_usecase,
    get_create_ticket_usecase,
)
from app.constants.ticket import TicketErrorDetail
from app.exceptions.event import (
    EventAlreadyOccurred,
    EventNotFound,
    EventUnexpectedStatus,
    RegistrationClosed,
)
from app.exceptions.ticket import (
    IdempotencyKeyConflict,
    SeatNotAvailable,
    TicketNotFound,
)
from app.schemas.api import (
    CancelTicketResponse,
    CreateTicketRequest,
    CreateTicketResponse,
)
from app.usecases.cancel_ticket import CancelTicketUsecase
from app.usecases.create_ticket import CreateTicketUsecase

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post(
    "",
    response_model=CreateTicketResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_ticket(
    payload: CreateTicketRequest,
    usecase: CreateTicketUsecase = Depends(get_create_ticket_usecase),
) -> CreateTicketResponse:
    try:
        ticket = await usecase.do(
            event_id=payload.event_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            seat=payload.seat,
        )
    except EventNotFound as exception:
        raise HTTPException(
            status_code=404, detail=TicketErrorDetail.event_not_found
        ) from exception
    except EventUnexpectedStatus as exception:
        raise HTTPException(
            status_code=409, detail=TicketErrorDetail.event_unexpected_status
        ) from exception
    except RegistrationClosed as exception:
        raise HTTPException(
            status_code=409, detail=TicketErrorDetail.registration_closed
        ) from exception
    except SeatNotAvailable as exception:
        raise HTTPException(
            status_code=409, detail=TicketErrorDetail.seat_not_available
        ) from exception
    except IdempotencyKeyConflict as exception:
        raise HTTPException(
            status_code=409,
            detail=TicketErrorDetail.idempotency_key_conflict.format(
                idempotency_key=ticket.idempotency_key
            ),
        ) from exception
    return CreateTicketResponse(ticket_id=ticket.id)


@router.delete("/{ticket_id}", response_model=CancelTicketResponse)
async def cancel_ticket(
    ticket_id: str,
    usecase: CancelTicketUsecase = Depends(get_cancel_ticket_usecase),
) -> CancelTicketResponse:
    try:
        success = await usecase.do(ticket_id)
    except TicketNotFound as exception:
        raise HTTPException(
            status_code=404, detail=TicketErrorDetail.ticket_not_found
        ) from exception
    except EventAlreadyOccurred as exception:
        raise HTTPException(
            status_code=409, detail=TicketErrorDetail.event_already_occurred
        ) from exception
    return CancelTicketResponse(success=success)
