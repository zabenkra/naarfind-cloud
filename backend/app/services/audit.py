import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.models import AuditLog, User


def record_audit(
    db: Session,
    *,
    user: User,
    action: str,
    entity_type: str,
    entity_id: int,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user.id,
        organization_id=user.organization_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(entry)
    db.flush()
    return entry
