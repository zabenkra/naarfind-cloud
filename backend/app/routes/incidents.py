from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_effective_organization_id
from app.models.models import Device, FireEvent, User
from app.schemas.fire_event_status import OPEN_INCIDENT_STATUSES
from app.schemas.fire_events import FireEventOut
from app.services.fire_events import to_fire_event_out
from app.services.tenant import fire_events_query

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])

OPEN_STATUS_VALUES = [s.value for s in OPEN_INCIDENT_STATUSES]


@router.get("", response_model=list[FireEventOut])
def list_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = get_effective_organization_id(current_user)

    if org_id is not None:
        rows = (
            fire_events_query(db, org_id)
            .filter(FireEvent.status.in_(OPEN_STATUS_VALUES))
            .order_by(FireEvent.created_at.desc())
            .all()
        )
    else:
        rows = (
            db.query(FireEvent, Device.name.label("device_name"))
            .outerjoin(Device, FireEvent.device_id == Device.id)
            .filter(FireEvent.status.in_(OPEN_STATUS_VALUES))
            .order_by(FireEvent.created_at.desc())
            .all()
        )

    return [to_fire_event_out(event, device_name) for event, device_name in rows]
