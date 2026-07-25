import datetime


def ensure_utc(value: datetime.datetime) -> datetime.datetime:
    """Возвращает timezone-aware datetime в UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=datetime.UTC)
    return value
