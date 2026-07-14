import uuid
import enum
import hashlib
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class MemberRole(str, enum.Enum):
    admin = "admin"
    mod = "mod"
    member = "member"


class CommunityPurpose(str, enum.Enum):
    education = "education"
    fun = "fun"
    technology = "technology"
    sports = "sports"
    gaming = "gaming"
    business = "business"
    other = "other"


def generate_unique_community_hash():
    """Generates a unique hash string for the community."""
    unique_id = str(uuid.uuid4())
    return hashlib.sha256(unique_id.encode()).hexdigest()[:10]


class Community(Base, TimestampMixin):
    __tablename__ = "communities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # The display name of the community
    name = Column(String(255), nullable=False)
    # A unique hashed name/identifier for the community
    unique_name = Column(String(255), unique=True, nullable=False, index=True, default=generate_unique_community_hash)
    
    about = Column(Text, nullable=True)
    purpose = Column(Enum(CommunityPurpose), default=CommunityPurpose.other, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    
    logo = Column(Text, nullable=True)
    banner = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # "communities_created" matches User.communities_created back_populates
    creator = relationship("User", back_populates="communities_created")
    members = relationship("CommunityMember", back_populates="community", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="community")
    conversations = relationship("Conversation", back_populates="community", cascade="all, delete-orphan")


class CommunityMember(Base):
    __tablename__ = "community_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id = Column(UUID(as_uuid=True), ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(MemberRole), default=MemberRole.member, nullable=False)
    joined_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    community = relationship("Community", back_populates="members")
    user = relationship("User", back_populates="community_memberships")


class JoinRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class CommunityJoinRequest(Base):
    __tablename__ = "community_join_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id = Column(UUID(as_uuid=True), ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(JoinRequestStatus), default=JoinRequestStatus.pending, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    community = relationship("Community")
    user = relationship("User")