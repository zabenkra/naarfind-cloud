from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

DeviceStatus = Literal["online", "warning", "offline"]


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: Optional[int] = None
    site_name: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    device_uid: str = Field(..., min_length=1, max_length=255)
    status: DeviceStatus = "offline"
    is_online: bool = False
    last_seen: Optional[datetime] = None
    cpu_temp: Optional[float] = None
    ram_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    camera_status: Optional[str] = None
    agent_version: Optional[str] = None
    created_at: Optional[datetime] = None
