from enum import StrEnum


class CapashinoErrorMessages(StrEnum):
    network_error = 'Ошибка соединения с Capashino: {exception}'
    reject = 'Capashino отклонил запрос с кодом {status_code}'
    unavailable = 'Capashino не доступен (код {status_code})'
