from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Device


def get_device_by_api_key(
    db: Session,
    device_uid: str,
    api_key: str,
) -> Device:
    device = db.query(Device).filter(Device.device_uid == device_uid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid device API key")
    return device
