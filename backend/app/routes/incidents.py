from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import (
    RequireOperator,
    RequireViewer,
    get_effective_organization_id,
)
from app.models.models import AuditLog, FireEvent, IncidentNote, User
from app.schemas.fire_event_status import OPEN_INCIDENT_STATUSES
from app.schemas.fire_events import FireEventOut
from app.schemas.incidents import (
    IncidentDetailOut,
    IncidentNoteCreate,
    IncidentNoteOut,
    IncidentStatusUpdate,
)
from app.services.audit import record_audit
from app.services.incidents import (
    build_timeline,
    get_incident_row,
    list_incidents_for_org,
    to_incident_detail,
)

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])

OPEN_STATUS_VALUES = [s.value for s in OPEN_INCIDENT_STATUSES]


@router.get("", response_model=list[FireEventOut])
def list_incidents(
    include_all: bool = Query(False, description="Include resolved and false_alarm"),
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireViewer),
):
    org_id = get_effective_organization_id(current_user)
    return list_incidents_for_org(
        db,
        org_id,
        include_all=include_all,
        open_status_values=OPEN_STATUS_VALUES,
    )


@router.get("/{incident_id}", response_model=IncidentDetailOut)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireViewer),
):
    org_id = get_effective_organization_id(current_user)
    event, device_name, site_name = get_incident_row(db, incident_id, org_id)

    notes = (
        db.query(IncidentNote)
        .options(joinedload(IncidentNote.user))
        .filter(IncidentNote.incident_id == incident_id)
        .order_by(IncidentNote.created_at.asc())
        .all()
    )

    audit_entries = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.user))
        .filter(
            AuditLog.entity_type == "incident",
            AuditLog.entity_id == incident_id,
        )
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    timeline = build_timeline(event, notes, audit_entries)
    return to_incident_detail(event, device_name, site_name, notes, timeline)


@router.patch("/{incident_id}/status", response_model=IncidentDetailOut)
def update_incident_status(
    incident_id: int,
    payload: IncidentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: RequireOperator,
):
    org_id = get_effective_organization_id(current_user)
    event, device_name, site_name = get_incident_row(db, incident_id, org_id)

    old_status = event.status
    new_status = payload.status.value
    if old_status == new_status:
        raise HTTPException(status_code=400, detail="Status is already set to this value")

    event.status = new_status
    record_audit(
        db,
        user=current_user,
        action="status_changed",
        entity_type="incident",
        entity_id=incident_id,
        metadata={"old_status": old_status, "new_status": new_status},
    )
    db.commit()

    return get_incident(incident_id, db=db, current_user=current_user)


@router.get("/{incident_id}/notes", response_model=list[IncidentNoteOut])
def list_incident_notes(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireViewer),
):
    org_id = get_effective_organization_id(current_user)
    get_incident_row(db, incident_id, org_id)

    notes = (
        db.query(IncidentNote)
        .options(joinedload(IncidentNote.user))
        .filter(IncidentNote.incident_id == incident_id)
        .order_by(IncidentNote.created_at.asc())
        .all()
    )

    return [
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


@router.post("/{incident_id}/notes", response_model=IncidentNoteOut, status_code=201)
def add_incident_note(
    incident_id: int,
    payload: IncidentNoteCreate,
    db: Session = Depends(get_db),
    current_user: RequireOperator,
):
    org_id = get_effective_organization_id(current_user)
    get_incident_row(db, incident_id, org_id)

    note = IncidentNote(
        incident_id=incident_id,
        user_id=current_user.id,
        message=payload.message.strip(),
    )
    db.add(note)
    db.flush()

    record_audit(
        db,
        user=current_user,
        action="note_added",
        entity_type="incident",
        entity_id=incident_id,
        metadata={"note_id": note.id},
    )
    db.commit()
    db.refresh(note)

    user = db.query(User).filter(User.id == current_user.id).first()
    return IncidentNoteOut(
        id=note.id,
        incident_id=note.incident_id,
        user_id=note.user_id,
        user_name=user.full_name if user else current_user.full_name,
        message=note.message,
        created_at=note.created_at,
    )
