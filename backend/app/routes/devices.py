from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_effective_organization_id
from app.models.models import Device, User
from app.schemas.devices import DeviceOut
from app.services.tenant import devices_query

router = APIRouter(prefix="/api/devices", tags=["Devices"])


@router.get("", response_model=list[DeviceOut])
def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = get_effective_organization_id(current_user)

    if org_id is not None:
        return devices_query(db, org_id).order_by(Device.created_at.desc()).all()

    return db.query(Device).order_by(Device.created_at.desc()).all()
