import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography

from .base import Base, TimestampMixin


# ── Gate ──────────────────────────────────────────────────────

class Gate(Base, TimestampMixin):
    __tablename__ = "gates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    society_name = Column(String(255), nullable=False, index=True)
    address = Column(Text, nullable=True)

    # PostGIS Point — (longitude, latitude), SRID 4326
    location = Column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    reviews = relationship("GateReview", back_populates="gate", cascade="all, delete-orphan")


# ── GateReview ────────────────────────────────────────────────

class GateReview(Base):
    """
    One review per (user, gate) pair recommended — add UniqueConstraint
    if you want to enforce single-review-per-user logic.
    """
    __tablename__ = "gate_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gate_id = Column(UUID(as_uuid=True), ForeignKey("gates.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    waiting_time = Column(Integer, nullable=True)
    parking = Column(Boolean, nullable=True)
    lift_available = Column(Boolean, nullable=True)
    delivery_difficulty = Column(Integer, nullable=True)
    guard_behavior = Column(Integer, nullable=True)
    entry_restrictions = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    overall_rating = Column(Integer, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    gate = relationship("Gate", back_populates="reviews")
    reviewer = relationship("User", back_populates="gate_reviews")