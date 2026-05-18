from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.fire_event_status import FireEventStatus
from app.schemas.validators import validate_media_url


class FireEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    device_name: Optional[str] = None
    confidence: float = Field(..., ge=0)
    event_type: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    temperature: Optional[float] = None
    status: str
    created_at: Optional[datetime] = None

    @field_validator("image_url", "video_url", mode="before")
    @classmethod
    def normalize_media_urls(cls, value):
        if value in (None, ""):
            return None
        return str(value)


class FireEventStatusUpdate(BaseModel):
    status: FireEventStatus = Field(
        ...,
        description="Event status: new, acknowledged, false_alarm, or resolved",
    )


class FireEventStatusResponse(BaseModel):
    id: int
    status: FireEventStatus
    message: str = "Status updated successfully"
