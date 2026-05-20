"""Device connectivity status from last_seen timestamp."""

from datetime import datetime, timezone
from typing import Literal, Optional

DeviceStatus = Literal["online", "warning", "offline"]

ONLINE_SECONDS = 60
WARNING_SECONDS = 300


def connection_status(
    last_seen: Optional[datetime],
    *,
    now: Optional[datetime] = None,
) -> DeviceStatus:
    if last_seen is None:
        return "offline"

    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    now = now or datetime.now(timezone.utc)
    age = (now - last_seen).total_seconds()

    if age < ONLINE_SECONDS:
        return "online"
    if age < WARNING_SECONDS:
        return "warning"
    return "offline"


def is_device_online(last_seen: Optional[datetime]) -> bool:
    return connection_status(last_seen) == "online"
