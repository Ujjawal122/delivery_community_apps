import uuid
import enum
from datetime import datetime, timezone
from typing import cast, Any

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum, DateTime, UniqueConstraint, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from shapely.geometry import Point

from .base import Base, TimestampMixin


class HazardSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class HazardStatus(str, enum.Enum):
    pending = "pending"
    resolved = "resolved"
    rejected = "rejected"


class HazardReport(Base, TimestampMixin):
    __tablename__ = "hazard_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, nullable=True)               # FK to a hazard_categories lookup if needed
    severity = Column(Enum(HazardSeverity), default=HazardSeverity.medium, nullable=False)
    status = Column(Enum(HazardStatus), default=HazardStatus.pending, nullable=False, index=True)

    location = Column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )

    reporter = relationship("User", back_populates="hazard_reports")
    images = relationship("HazardImage", back_populates="hazard", cascade="all, delete-orphan")
    votes = relationship("HazardVote", back_populates="hazard", cascade="all, delete-orphan")

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)


class HazardImage(Base):
    __tablename__ = "hazard_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hazard_id = Column(UUID(as_uuid=True), ForeignKey("hazard_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    hazard = relationship("HazardReport", back_populates="images")


class HazardVote(Base):
    """One row per (user, hazard) pair."""
    __tablename__ = "hazard_votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    hazard_id = Column(UUID(as_uuid=True), ForeignKey("hazard_reports.id", ondelete="CASCADE"), nullable=False)
    vote_type = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "hazard_id", name="uq_hazard_vote_user_hazard"),)

    # "hazard_votes" matches User.hazard_votes back_populates
    user = relationship("User", back_populates="hazard_votes")
    hazard = relationship("HazardReport", back_populates="votes")