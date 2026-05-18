#!/usr/bin/env python3
"""
Create the first super_admin user.

Usage:
  cd backend
  python scripts/create_super_admin.py --email admin@naarfind.cloud --password 'YourSecurePass123!' --name 'Platform Admin' --org 'NaarFind Platform'
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.models import Organization, User, UserRole


def main():
    parser = argparse.ArgumentParser(description="Create NaarFind super_admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", default="Super Admin")
    parser.add_argument("--org", default="NaarFind Platform")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        email = args.email.lower().strip()
        if db.query(User).filter(User.email == email).first():
            print(f"User {email} already exists")
            return 1

        org = db.query(Organization).filter(Organization.name == args.org).first()
        if not org:
            org = Organization(name=args.org)
            db.add(org)
            db.flush()

        user = User(
            organization_id=org.id,
            full_name=args.name,
            email=email,
            hashed_password=hash_password(args.password),
            role=UserRole.SUPER_ADMIN.value,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"Created super_admin: {email} (org_id={org.id}, user_id={user.id})")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
