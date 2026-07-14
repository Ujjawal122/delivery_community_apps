from sqlalchemy import Text, String, Boolean, Integer, Float
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
    username: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vehicle_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    follower_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    following_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    
    # New fields for personalized feed
    location = mapped_column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    interests = mapped_column(PG_ARRAY(String), nullable=True)
    
    # Push notifications
    push_token = mapped_column(String(255), nullable=True)


    latitude = mapped_column(Float, nullable=True)
    longitude = mapped_column(Float, nullable=True)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", foreign_keys="Notification.user_id", back_populates="user", cascade="all, delete-orphan")
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
    conversation_memberships = relationship("ConversationMember", back_populates="user", cascade="all, delete-orphan")
    messages_sent = relationship("Message", back_populates="sender", cascade="all, delete-orphan")
    
    followers = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following", cascade="all, delete-orphan")
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower", cascade="all, delete-orphan")
