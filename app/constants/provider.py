from enum import StrEnum


class ProviderLogMessage(StrEnum):
    http_error = (
        'Events Provider вернул ошибку {status_code}'
        ' для {method} {url}: {body}'
    )
    connection_error = 'Ошибка соединения с Events Provider: {error}'
    non_json_response = (
        'Events Provider вернул ответ не в формате JSON'
        ' для {method} {url}: {body}'
    )
    rate_limited_retry = (
        'Events Provider вернул ошибку 429 для %(method)s %(url)s,'
        ' повтор через %(interval).1f сек'
    )
