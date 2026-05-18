from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_effective_organization_id, is_super_admin
from app.models.models import Device, FireEvent, Site, User
from app.schemas.dashboard import DashboardStats
from app.schemas.fire_event_status import OPEN_INCIDENT_STATUSES
from app.services.tenant import devices_query, fire_events_query

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

OPEN_STATUS_VALUES = [s.value for s in OPEN_INCIDENT_STATUSES]


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = get_effective_organization_id(current_user)

    if org_id is not None:
        device_q = devices_query(db, org_id)
        event_q = fire_events_query(db, org_id)
        total_devices = device_q.count()
        online_devices = device_q.filter(Device.is_online.is_(True)).count()
        fire_events = event_q.count()
        open_incidents = event_q.filter(FireEvent.status.in_(OPEN_STATUS_VALUES)).count()
    else:
        total_devices = db.query(Device).count()
        online_devices = db.query(Device).filter(Device.is_online.is_(True)).count()
        fire_events = db.query(FireEvent).count()
        open_incidents = (
            db.query(FireEvent)
            .filter(FireEvent.status.in_(OPEN_STATUS_VALUES))
            .count()
        )

    return DashboardStats(
        total_devices=total_devices,
        online_devices=online_devices,
        fire_events=fire_events,
        open_incidents=open_incidents,
    )
