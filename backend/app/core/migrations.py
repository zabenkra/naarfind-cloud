"""Lightweight schema patches for existing databases (no Alembic)."""

import logging

from sqlalchemy import text

from app.core.database import engine

logger = logging.getLogger(__name__)

_DEVICE_COLUMNS = (
    ("cpu_temp", "DOUBLE PRECISION"),
    ("ram_usage", "DOUBLE PRECISION"),
    ("disk_usage", "DOUBLE PRECISION"),
    ("camera_status", "VARCHAR(64)"),
    ("agent_version", "VARCHAR(64)"),
)


def ensure_device_telemetry_columns() -> None:
    with engine.begin() as conn:
        for column, col_type in _DEVICE_COLUMNS:
            conn.execute(
                text(
                    f"ALTER TABLE devices ADD COLUMN IF NOT EXISTS {column} {col_type}"
                )
            )
    logger.info("Device telemetry columns verified")


def ensure_incident_tables() -> None:
    """Create incident_notes and audit_logs if missing (SQLAlchemy create_all also runs)."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS incident_notes (
                    id SERIAL PRIMARY KEY,
                    incident_id INTEGER NOT NULL REFERENCES fire_events(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    message VARCHAR NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    organization_id INTEGER NOT NULL REFERENCES organizations(id),
                    action VARCHAR(64) NOT NULL,
                    entity_type VARCHAR(64) NOT NULL,
                    entity_id INTEGER NOT NULL,
                    metadata VARCHAR,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_incident_notes_incident_id ON incident_notes (incident_id)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_audit_logs_entity ON audit_logs (entity_type, entity_id)"
            )
        )
    logger.info("Incident notes and audit log tables verified")
