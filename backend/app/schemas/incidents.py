from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.fire_event_status import FireEventStatus


class IncidentStatusUpdate(BaseModel):
    status: FireEventStatus = Field(
        ...,
        description="new, acknowledged, investigating, resolved, false_alarm",
    )


class IncidentNoteCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class IncidentNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    user_id: int
    user_name: Optional[str] = None
    message: str
    created_at: Optional[datetime] = None


class TimelineEntry(BaseModel):
    id: str
    type: str
    action: Optional[str] = None
    message: Optional[str] = None
    user_name: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime


class IncidentDeviceOut(BaseModel):
    id: int
    device_uid: str
    name: str


class IncidentSiteOut(BaseModel):
    id: int
    name: str


class IncidentDetailOut(BaseModel):
    """Fire event (incident) detail — incident_id is fire_events.id."""

    id: int
    device_id: int
    device_name: Optional[str] = None
    site_name: Optional[str] = None
    device: Optional[IncidentDeviceOut] = None
    site: Optional[IncidentSiteOut] = None
    confidence: float
    event_type: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    temperature: Optional[float] = None
    status: str
    created_at: Optional[datetime] = None
    notes: list[IncidentNoteOut] = []
    timeline: list[TimelineEntry] = []
