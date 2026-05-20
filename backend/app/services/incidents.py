import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.models import AuditLog, Device, FireEvent, IncidentNote, Site
from app.schemas.fire_events import FireEventOut
from app.schemas.incidents import (
    IncidentDetailOut,
    IncidentDeviceOut,
    IncidentNoteOut,
    IncidentSiteOut,
    TimelineEntry,
)
from app.services.fire_events import to_fire_event_out
from app.services.tenant import fire_events_query

INCIDENT_NOT_FOUND = "Incident not found or you do not have access"


def _parse_metadata(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def get_incident_context(
    db: Session,
    incident_id: int,
    organization_id: int | None,
) -> tuple[FireEvent, Device | None, Site | None]:
    """Load fire event by id (incident_id). Org users are scoped via device site."""
    event = (
        db.query(FireEvent)
        .options(joinedload(FireEvent.device).joinedload(Device.site))
        .filter(FireEvent.id == incident_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail=INCIDENT_NOT_FOUND)

    device = event.device
    site = device.site if device else None

    if organization_id is not None:
        if not site or site.organization_id != organization_id:
            raise HTTPException(status_code=404, detail=INCIDENT_NOT_FOUND)

    return event, device, site


def get_incident_row(
    db: Session,
    incident_id: int,
    organization_id: int | None,
) -> tuple[FireEvent, str | None, str | None]:
    """Backward-compatible tuple for callers that only need names."""
    event, device, site = get_incident_context(db, incident_id, organization_id)
    return event, device.name if device else None, site.name if site else None


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
    device: Device | None,
    site: Site | None,
    notes: list[IncidentNote],
    timeline: list[TimelineEntry],
) -> IncidentDetailOut:
    device_name = device.name if device else None
    site_name = site.name if site else None
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
        device=(
            IncidentDeviceOut(
                id=device.id,
                device_uid=device.device_uid,
                name=device.name,
            )
            if device
            else None
        ),
        site=(
            IncidentSiteOut(id=site.id, name=site.name) if site else None
        ),
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


def load_incident_detail(
    db: Session,
    incident_id: int,
    organization_id: int | None,
    *,
    audit_organization_id: int | None = None,
) -> IncidentDetailOut:
    """Full incident payload for GET detail and PATCH status responses."""
    event, device, site = get_incident_context(db, incident_id, organization_id)

    notes = (
        db.query(IncidentNote)
        .options(joinedload(IncidentNote.user))
        .filter(IncidentNote.incident_id == incident_id)
        .order_by(IncidentNote.created_at.asc())
        .all()
    )

    audit_q = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.user))
        .filter(
            AuditLog.entity_type == "incident",
            AuditLog.entity_id == incident_id,
        )
    )
    if audit_organization_id is not None:
        audit_q = audit_q.filter(AuditLog.organization_id == audit_organization_id)

    audit_entries = audit_q.order_by(AuditLog.created_at.asc()).all()
    timeline = build_timeline(event, notes, audit_entries)
    return to_incident_detail(event, device, site, notes, timeline)


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
