from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.validators import validate_media_url


class FireEventCreate(BaseModel):
    device_uid: str = Field(..., min_length=1, max_length=255)
    confidence: float = Field(..., ge=0, le=1)
    event_type: str = Field(default="fire_detected", max_length=100)
    image_url: Optional[str] = Field(default=None, max_length=2048)
    video_url: Optional[str] = Field(default=None, max_length=2048)
    temperature: Optional[float] = None

    @field_validator("image_url", mode="before")
    @classmethod
    def validate_image_url(cls, value):
        return validate_media_url(value, "image_url")

    @field_validator("video_url", mode="before")
    @classmethod
    def validate_video_url(cls, value):
        return validate_media_url(value, "video_url")
