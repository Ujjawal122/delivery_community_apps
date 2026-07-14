import uuid
import enum
from typing import Any, cast
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Integer, ForeignKey, UniqueConstraint, Enum, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from shapely.geometry import Point

from .base import Base, TimestampMixin


class VoteType(int, enum.Enum):
    up = 1
    down = -1


class PostType(str, enum.Enum):
    """7 community post categories matching the Delivery Community design."""
    question       = "question"        # Ask Questions
    share          = "share"           # Share
    discussion     = "discussion"      # Daily Discussion
    meme           = "meme"            # Memes
    tip            = "tip"             # Tips
    news           = "news"            # News
    company_update = "company_update"  # Company Updates


# ── Post ──────────────────────────────────────────────────────

class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    community_id = Column(UUID(as_uuid=True), ForeignKey("communities.id", ondelete="SET NULL"), nullable=True, index=True)
    post_type = Column(Enum(PostType), default=PostType.share, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    image = Column(Text, nullable=True)                        # CDN URL
    video = Column(Text, nullable=True)                        # CDN URL
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    upvotes_count = Column(Integer, default=0, nullable=False)
    downvotes_count = Column(Integer, default=0, nullable=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    author = relationship("User", back_populates="posts")
    community = relationship("Community", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    votes = relationship("PostVote", back_populates="post", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="post", cascade="all, delete-orphan")


class PostVote(Base):
    """One row per (user, post) pair — enforced by unique constraint."""
    __tablename__ = "post_votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    vote_type = Column(Integer, nullable=False)                # 1 = up, -1 = down

    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_post_vote_user_post"),)

    user = relationship("User", back_populates="post_votes")
    post = relationship("Post", back_populates="votes")


class Comment(Base, TimestampMixin):
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)  # nested replies
    replied_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    upvotes_count = Column(Integer, default=0, nullable=False)
    downvotes_count = Column(Integer, default=0, nullable=False)

    post = relationship("Post", back_populates="comments")
    author = relationship("User", foreign_keys=[user_id], back_populates="comments")
    replied_to_user = relationship("User", foreign_keys=[replied_to_user_id])
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Comment", back_populates="replies", remote_side="Comment.id")
    votes = relationship("CommentVote", back_populates="comment", cascade="all, delete-orphan")


class CommentVote(Base):
    """One row per (user, comment) pair."""
    __tablename__ = "comment_votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)
    vote_type = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "comment_id", name="uq_comment_vote_user_comment"),)

    user = relationship("User", back_populates="comment_votes")
    comment = relationship("Comment", back_populates="votes")


# ── Bookmark ──────────────────────────────────────────────────

class Bookmark(Base):
    """One row per (user, post) pair — user can bookmark any post once."""
    __tablename__ = "bookmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_bookmark_user_post"),)

    user = relationship("User", back_populates="bookmarks")
    post = relationship("Post", back_populates="bookmarks")