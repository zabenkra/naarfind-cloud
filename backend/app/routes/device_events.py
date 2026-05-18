from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Device, FireEvent
from app.schemas.device_events import FireEventCreate
from app.schemas.fire_event_status import FireEventStatus
from app.services.broadcast import broadcast_fire_event

router = APIRouter(prefix="/api/device", tags=["Device Events"])

# TODO(production): rate-limit device ingest (e.g. slowapi — 60/min per device API key)

@router.post("/events/fire")
async def create_fire_event(
    payload: FireEventCreate,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.device_uid == payload.device_uid).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if device.api_key != x_api_key:
        raise HTTPException(status_code=401, detail="Invalid device API key")

    device.is_online = True
    device.last_seen = datetime.now(timezone.utc)

    event = FireEvent(
        device_id=device.id,
        confidence=payload.confidence,
        event_type=payload.event_type,
        image_url=payload.image_url,
        video_url=payload.video_url,
        temperature=payload.temperature,
        status=FireEventStatus.NEW.value,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    await broadcast_fire_event(event, device, db)

    return {
        "message": "Fire event received",
        "event_id": event.id,
        "status": event.status
    }