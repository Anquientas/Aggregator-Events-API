from enum import StrEnum


class WorkerLogMessage(StrEnum):
    worker_started = (
        'Фоновый воркер синхронизации запущен, интервал: %(interval)s с'
    )
    sync_already_running = 'Синхронизация уже выполняется, пропускаем запуск'
    unexpected_worker_error = (
        'Неучтенная ошибка в фоновом воркере синхронизации'
    )
