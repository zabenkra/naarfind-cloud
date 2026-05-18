from enum import Enum


class FireEventStatus(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    FALSE_ALARM = "false_alarm"
    RESOLVED = "resolved"


OPEN_INCIDENT_STATUSES = (
    FireEventStatus.NEW,
    FireEventStatus.ACKNOWLEDGED,
)
