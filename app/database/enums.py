import enum


class SyncStatus(enum.StrEnum):
    idle = "idle"
    running = "running"
    success = "success"
    failed = "failed"
