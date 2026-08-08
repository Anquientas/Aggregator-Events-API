from enum import StrEnum


class EventStatus(StrEnum):
    new = 'new'
    published = 'published'
    cancelled = 'cancelled'
