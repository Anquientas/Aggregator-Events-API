from enum import StrEnum


class OutboxTypes(StrEnum):
    notification = 'notification'


class OutboxStatus(StrEnum):
    pending = 'pending'
    sent = 'sent'
    failed = 'failed'
