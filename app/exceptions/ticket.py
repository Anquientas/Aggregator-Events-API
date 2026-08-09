class SeatNotAvailable(Exception):
    pass


class TicketNotFound(Exception):
    pass


class IdempotencyKeyConflict(Exception):
    """
    Ошибка отличия данных запроса от сохраненных
    при совпадении idempotency_key.
    """
    pass


class DuplicateIdempotencyKey(Exception):
    """Ошибка-индикатор проигрыша гонки двойного клика."""
    pass
