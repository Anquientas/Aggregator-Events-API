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
        ' {exception}'
    )
