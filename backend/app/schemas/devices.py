from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    device_uid: str = Field(..., min_length=1, max_length=255)
    is_online: bool
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
