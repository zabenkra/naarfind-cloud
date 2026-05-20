import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import IS_PRODUCTION, cors_origins, validate_production_settings
from app.core.database import Base, check_database_connection, engine, get_db
from app.models import models  # noqa: F401 - registers models with SQLAlchemy metadata
from app.routes import auth, dashboard, device_events, devices, fire_events, incidents
from app.websocket import routes as websocket_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.config import DATABASE_HOST, PORT

    validate_production_settings()
    logger.info(
        "Starting NaarFind API env=%s port=%s database_host=%s cors=%s",
        "production" if IS_PRODUCTION else "development",
        PORT,
        DATABASE_HOST,
        cors_origins(),
    )
    try:
        check_database_connection()
        logger.info("Database connection OK")
    except Exception as exc:
        logger.error("Database connection failed on startup: %s", exc)
        if IS_PRODUCTION:
            raise
    Base.metadata.create_all(bind=engine)
    from app.core.migrations import ensure_device_telemetry_columns, ensure_incident_tables

    ensure_device_telemetry_columns()
    ensure_incident_tables()
    yield


app = FastAPI(title="NaarFind API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: add rate limiting for /api/auth/* and /api/device/* (e.g. slowapi)

app.include_router(auth.router)
# Device ingest: POST /api/device/heartbeat, POST /api/device/events/fire
app.include_router(device_events.router)
app.include_router(dashboard.router)
app.include_router(devices.router)
app.include_router(fire_events.router)
app.include_router(incidents.router)
app.include_router(websocket_routes.router)


@app.get("/")
def root():
    return {"message": "NaarFind Cloud API Running", "environment": "production" if IS_PRODUCTION else "development"}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as exc:
        logger.warning("Health check failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "database": "disconnected"},
        ) from exc
