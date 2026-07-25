class EventsProviderError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class EventNotFound(Exception):
    pass


class EventUnexpectedStatus(Exception):
    pass


class SeatNotAvailable(Exception):
    pass


class RegistrationClosed(Exception):
    pass


class EventAlreadyOccurred(Exception):
    pass


class TicketNotFound(Exception):
    pass
