from enum import Enum


class FireEventStatus(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_ALARM = "false_alarm"


OPEN_INCIDENT_STATUSES = (
    FireEventStatus.NEW,
    FireEventStatus.ACKNOWLEDGED,
    FireEventStatus.INVESTIGATING,
)

ALL_INCIDENT_STATUSES = tuple(FireEventStatus)
