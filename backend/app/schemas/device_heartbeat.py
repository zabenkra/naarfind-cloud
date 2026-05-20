from typing import Optional

from pydantic import BaseModel, Field


class HeartbeatPayload(BaseModel):
    """POST /api/device/heartbeat body."""

    device_uid: str = Field(..., min_length=1, max_length=255)
    agent_version: Optional[str] = Field(default=None, max_length=64)
    cpu_temp: Optional[float] = Field(default=None, ge=-50, le=150)
    camera_status: Optional[str] = Field(default=None, max_length=64)
    disk_usage: Optional[float] = Field(default=None, ge=0, le=100)
    ram_usage: Optional[float] = Field(default=None, ge=0, le=100)


# Backward-compatible alias
DeviceHeartbeatIn = HeartbeatPayload
