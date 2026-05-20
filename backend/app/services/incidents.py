import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import AuditLog, Device, FireEvent, IncidentNote, Site, User
from app.schemas.fire_events import FireEventOut
from app.schemas.incidents import IncidentDetailOut, IncidentNoteOut, TimelineEntry
from app.services.fire_events import to_fire_event_out
from app.services.tenant import fire_events_query, get_fire_event_for_org


def _parse_metadata(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def get_incident_row(
    db: Session,
    incident_id: int,
    organization_id: int | None,
) -> tuple[FireEvent, str | None, str | None]:
    if organization_id is not None:
        row = (
            db.query(FireEvent, Device.name, Site.name)
            .join(Device, FireEvent.device_id == Device.id)
            .join(Site, Device.site_id == Site.id)
            .filter(
                Site.organization_id == organization_id,
                FireEvent.id == incident_id,
            )
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Incident not found")
        event, device_name, site_name = row
        return event, device_name, site_name

    row = (
        db.query(FireEvent, Device.name, Site.name)
        .join(Device, FireEvent.device_id == Device.id)
        .outerjoin(Site, Device.site_id == Site.id)
        .filter(FireEvent.id == incident_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Incident not found")
    return row[0], row[1], row[2]


def build_timeline(
    event: FireEvent,
    notes: list[IncidentNote],
    audit_entries: list[AuditLog],
) -> list[TimelineEntry]:
    items: list[TimelineEntry] = []

    if event.created_at:
        items.append(
            TimelineEntry(
                id=f"created-{event.id}",
                type="created",
                action="incident_opened",
                message="Fire incident detected and logged",
                created_at=event.created_at,
            )
        )

    for entry in audit_entries:
        meta = _parse_metadata(entry.metadata_json)
        user_name = entry.user.full_name if entry.user else None
        message = None
        if entry.action == "status_changed" and meta:
            message = f"Status changed to {meta.get('new_status', '')}"
        items.append(
            TimelineEntry(
                id=f"audit-{entry.id}",
                type="audit",
                action=entry.action,
                message=message,
                user_name=user_name,
                metadata=meta,
                created_at=entry.created_at,
            )
        )

    for note in notes:
        items.append(
            TimelineEntry(
                id=f"note-{note.id}",
                type="note",
                message=note.message,
                user_name=note.user.full_name if note.user else None,
                created_at=note.created_at,
            )
        )

    items.sort(key=lambda x: x.created_at)
    return items


def to_incident_detail(
    event: FireEvent,
    device_name: str | None,
    site_name: str | None,
    notes: list[IncidentNote],
    timeline: list[TimelineEntry],
) -> IncidentDetailOut:
    note_outs = [
        IncidentNoteOut(
            id=n.id,
            incident_id=n.incident_id,
            user_id=n.user_id,
            user_name=n.user.full_name if n.user else None,
            message=n.message,
            created_at=n.created_at,
        )
        for n in notes
    ]
    return IncidentDetailOut(
        id=event.id,
        device_id=event.device_id,
        device_name=device_name,
        site_name=site_name,
        confidence=event.confidence,
        event_type=event.event_type,
        image_url=event.image_url,
        video_url=event.video_url,
        temperature=event.temperature,
        status=event.status,
        created_at=event.created_at,
        notes=note_outs,
        timeline=timeline,
    )


def list_incidents_for_org(
    db: Session,
    organization_id: int | None,
    *,
    include_all: bool = False,
    open_status_values: list[str],
) -> list[FireEventOut]:
    if organization_id is not None:
        q = fire_events_query(db, organization_id)
        if not include_all:
            q = q.filter(FireEvent.status.in_(open_status_values))
        rows = q.order_by(FireEvent.created_at.desc()).limit(200).all()
    else:
        q = db.query(FireEvent, Device.name.label("device_name")).outerjoin(
            Device, FireEvent.device_id == Device.id
        )
        if not include_all:
            q = q.filter(FireEvent.status.in_(open_status_values))
        rows = q.order_by(FireEvent.created_at.desc()).limit(200).all()

    return [to_fire_event_out(event, device_name) for event, device_name in rows]
