from app.models.models import FireEvent
from app.schemas.fire_events import FireEventOut


def to_fire_event_out(event: FireEvent, device_name: str | None) -> FireEventOut:
    return FireEventOut(
        id=event.id,
        device_id=event.device_id,
        device_name=device_name,
        confidence=event.confidence,
        event_type=event.event_type,
        image_url=event.image_url,
        video_url=event.video_url,
        temperature=event.temperature,
        status=event.status,
        created_at=event.created_at,
    )
