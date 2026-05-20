import enum

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="organization")
    sites = relationship("Site", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default=UserRole.VIEWER.value)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="users")


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="sites")
    devices = relationship("Device", back_populates="site")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True)
    name = Column(String, nullable=False)
    device_uid = Column(String, unique=True, index=True, nullable=False)
    api_key = Column(String, nullable=False)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime(timezone=True))
    cpu_temp = Column(Float)
    ram_usage = Column(Float)
    disk_usage = Column(Float)
    camera_status = Column(String(64))
    agent_version = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    site = relationship("Site", back_populates="devices")
    fire_events = relationship("FireEvent", back_populates="device")


class FireEvent(Base):
    __tablename__ = "fire_events"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    event_type = Column(String, default="fire_detected")
    image_url = Column(String)
    video_url = Column(String)
    temperature = Column(Float)
    status = Column(String, default="new")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    device = relationship("Device", back_populates="fire_events")
    notes = relationship(
        "IncidentNote",
        back_populates="incident",
        cascade="all, delete-orphan",
    )


class IncidentNote(Base):
    __tablename__ = "incident_notes"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("fire_events.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    incident = relationship("FireEvent", back_populates="notes")
    user = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    action = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(Integer, nullable=False, index=True)
    metadata_json = Column("metadata", String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
