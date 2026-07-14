import uuid
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin

class Follow(Base, TimestampMixin):
    __tablename__ = "follows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    follower_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    following_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
  
    status = Column(String(20), default="accepted", nullable=False)

    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', name='uq_follower_following'),
        CheckConstraint('follower_id != following_id', name='ck_no_self_follow'),
    )

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following = relationship("User", foreign_keys=[following_id], back_populates="followers")
