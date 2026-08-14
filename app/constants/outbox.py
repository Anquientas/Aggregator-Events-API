from enum import StrEnum


class OutboxTypes(StrEnum):
    notification = 'notification'


class OutboxStatus(StrEnum):
    pending = 'pending'
    sent = 'sent'
    failed = 'failed'


class OutboxLogMessage(StrEnum):
    unexpected_dispatcher_error = (
        'Неучтенная ошибка в фоновом воркере отправки уведомлений:'
        ' %(exception)s'
    )
    unexpected_record_error = (
        'Неучтенная ошибка при обработке записи outbox с id %(record_id)s:'
        ' %(exception)s'
    )


class OutboxErrorMessage(StrEnum):
    attempts_exceeded = (
        'Превышено число попыток отправки ({attempts_number})'
    )
