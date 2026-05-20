from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Device, FireEvent
from app.schemas.device_events import FireEventCreate
from app.schemas.device_heartbeat import HeartbeatPayload
from app.schemas.fire_event_status import FireEventStatus
from app.services.broadcast import broadcast_device_heartbeat, broadcast_fire_event
from app.services.device_auth import get_device_by_api_key

router = APIRouter(prefix="/api/device", tags=["Device Events"])

# TODO(production): rate-limit device ingest (e.g. slowapi — 60/min per device API key)


@router.get("/heartbeat", include_in_schema=False)
def device_heartbeat_get():
    """Reject mistaken GET requests from agents or health checks."""
    raise HTTPException(
        status_code=405,
        detail="Method not allowed. Use POST /api/device/heartbeat with JSON body and X-API-KEY header.",
    )


@router.post(
    "/heartbeat",
    summary="Device heartbeat",
    response_description="Heartbeat accepted",
)
async def device_heartbeat(
    payload: HeartbeatPayload,
    x_api_key: str = Header(..., alias="X-API-KEY"),
    db: Session = Depends(get_db),
):
    """
    Raspberry Pi edge-agent heartbeat.

    Header: `X-API-KEY` (case-insensitive).
    """
    device = get_device_by_api_key(db, payload.device_uid, x_api_key)
    now = datetime.now(timezone.utc)

    device.last_seen = now
    device.is_online = True
    device.agent_version = payload.agent_version
    device.cpu_temp = payload.cpu_temp
    device.camera_status = payload.camera_status
    device.disk_usage = payload.disk_usage
    device.ram_usage = payload.ram_usage

    db.commit()
    db.refresh(device)

    await broadcast_device_heartbeat(device, db)

    return {
        "message": "Heartbeat received",
        "device_uid": device.device_uid,
        "status": "online",
    }


@router.post("/events/fire")
async def create_fire_event(
    payload: FireEventCreate,
    x_api_key: str = Header(..., alias="X-API-KEY"),
    db: Session = Depends(get_db),
):
    device = get_device_by_api_key(db, payload.device_uid, x_api_key)
    now = datetime.now(timezone.utc)

    device.is_online = True
    device.last_seen = now

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
        "status": event.status,
    }
