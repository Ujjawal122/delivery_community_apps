from sqlalchemy import Text, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY as PG_ARRAY
from geoalchemy2 import Geometry
from typing import cast, Any
from shapely.geometry import Point
import uuid
from .base import Base, TimestampMixin



class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vehicle_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # New fields for personalized feed
    location = mapped_column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    interests = mapped_column(PG_ARRAY(String), nullable=True)
    
    # Push notifications
    push_token = mapped_column(String(255), nullable=True)


    @property
    def latitude(self) -> float | None:
        if self.location is None:
            return None
        from geoalchemy2.shape import to_shape
        point=cast(Point, to_shape(cast(Any, self.location)))
        return point.y

    @property
    def longitude(self) -> float | None:
        if self.location is None:
            return None
        from geoalchemy2.shape import to_shape
        point=cast(Point, to_shape(cast(Any, self.location)))
        return point.x

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    communities_created = relationship("Community", back_populates="creator")
    community_memberships = relationship("CommunityMember", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    post_votes = relationship("PostVote", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", foreign_keys="Comment.user_id", back_populates="author", cascade="all, delete-orphan")
    comment_votes = relationship("CommentVote", back_populates="user", cascade="all, delete-orphan")
    hazard_reports = relationship("HazardReport", back_populates="reporter", cascade="all, delete-orphan")
    hazard_votes = relationship("HazardVote", back_populates="user", cascade="all, delete-orphan")
    gate_reviews = relationship("GateReview", back_populates="reviewer", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
