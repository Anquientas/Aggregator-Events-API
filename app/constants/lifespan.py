from enum import StrEnum


class LifespanLogMessage(StrEnum):
    startup_begin = (
        'Инициализация ресурсов приложения (провайдер, кэш, фоновый воркер)'
    )
    shutdown_begin = (
        'Остановка приложения: останавливаем воркер и закрываем HTTP-клиент'
    )
