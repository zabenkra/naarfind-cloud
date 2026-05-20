"""
One-time seed for the production Pi device (pi-001).

Usage:
  cd backend
  DATABASE_URL=... python scripts/seed_pi_device.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal
from app.models.models import Device, Organization, Site

DEVICE_UID = os.getenv("DEVICE_UID", "pi-001")
DEVICE_NAME = os.getenv("DEVICE_NAME", "Raspberry Pi 01")
DEVICE_API_KEY = os.getenv("DEVICE_API_KEY", "SUPER_SECRET_KEY_123")
SITE_NAME = os.getenv("SITE_NAME", "Main Site")


def main() -> None:
    db = SessionLocal()
    try:
        org = db.query(Organization).order_by(Organization.id.asc()).first()
        if not org:
            print("No organization found — register a user in the app first.")
            return

        site = (
            db.query(Site)
            .filter(Site.organization_id == org.id, Site.name == SITE_NAME)
            .first()
        )
        if not site:
            site = Site(organization_id=org.id, name=SITE_NAME)
            db.add(site)
            db.flush()
            print(f"Created site: {SITE_NAME}")

        device = db.query(Device).filter(Device.device_uid == DEVICE_UID).first()
        if device:
            device.name = DEVICE_NAME
            device.site_id = site.id
            device.api_key = DEVICE_API_KEY
            print(f"Updated device {DEVICE_UID}")
        else:
            device = Device(
                site_id=site.id,
                name=DEVICE_NAME,
                device_uid=DEVICE_UID,
                api_key=DEVICE_API_KEY,
                is_online=False,
            )
            db.add(device)
            print(f"Created device {DEVICE_UID}")

        db.commit()
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
