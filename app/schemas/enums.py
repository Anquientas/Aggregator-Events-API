import enum


class HealthStatus(enum.StrEnum):
    ok = "ok"


class SyncTriggerStatus(enum.StrEnum):
    triggered = "triggered"
