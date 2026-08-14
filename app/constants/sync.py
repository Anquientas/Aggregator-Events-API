from enum import StrEnum


class SyncStatus(StrEnum):
    idle = 'idle'
    running = 'running'
    success = 'success'
    failed = 'failed'


class SyncTriggerStatus(StrEnum):
    triggered = 'triggered'


class SyncLogMessage(StrEnum):
    started = 'Синхронизация запущена, changed_at=%(change_at)s'
    finished_ok = (
        'Синхронизация завершена успешно, обработано событий: %(number)s'
    )
    failed = 'Синхронизация завершилась с ошибкой'
    event_skipped = (
        'Событие %(event_id)s пропущено из-за ошибки при сохранении'
    )
