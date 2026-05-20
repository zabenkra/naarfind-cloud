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
