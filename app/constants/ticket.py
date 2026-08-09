from enum import StrEnum


class TicketErrorDetail(StrEnum):
    event_not_found = 'Событие не найдено'
    event_unexpected_status = (
        'Регистрация недоступна для события в этом статусе'
    )
    registration_closed = 'Дедлайн регистрации на это событие уже прошёл'
    seat_not_available = 'Выбранное место уже занято'
    ticket_not_found = 'Регистрация не найдена'
    event_already_occurred = (
        'Нельзя отменить регистрацию — мероприятие уже прошло'
    )
    idempotency_key_conflict = (
        'Запрос с idempotency_key {idempotency_key}'
        ' уже обработан с другими данными'
    )


class TicketNotificationMessage(StrEnum):
    registration = (
        'Вы успешно зарегистрированы на "{event_name}",'
        ' {event_time}, место {seat}'
    )


class EventErrorDetail(StrEnum):
    event_not_found = 'Событие не найдено'
    seats_unavailable_status = (
        'Места доступны только для опубликованных событий'
    )
