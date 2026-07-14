"""
app/schemas/post.py
Pydantic schemas for Posts, Comments, Votes, and Bookmarks.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.post import PostType


# ── Shared author snippet ──────────────────────────────────────────

class AuthorSnippet(BaseModel):
    """Minimal author info embedded inside post/comment responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    avatar: Optional[str] = None


# ── Post schemas ───────────────────────────────────────────────────

class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="Post title")
    content: Optional[str] = Field(None, description="Post body text")
    post_type: PostType = Field(PostType.share, description="Category of the post")
    image: Optional[str] = Field(None, description="CDN image URL")
    video: Optional[str] = Field(None, description="CDN video URL")
    community_id: Optional[UUID] = Field(None, description="Community to post in (optional)")
    latitude: Optional[float] = Field(None, description="Post latitude")
    longitude: Optional[float] = Field(None, description="Post longitude")


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    image: Optional[str] = None
    video: Optional[str] = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    content: Optional[str] = None
    post_type: PostType
    image: Optional[str] = None
    video: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    upvotes_count: int
    downvotes_count: int
    user_vote: Optional[int] = None
    community_id: Optional[UUID] = None
    author: AuthorSnippet
    created_at: datetime
    updated_at: datetime


class PaginatedPosts(BaseModel):
    items: List[PostResponse]
    total: int
    page: int
    limit: int


# ── Vote schemas ───────────────────────────────────────────────────

class VoteRequest(BaseModel):
    vote_type: Literal["up", "down"] = Field(..., description="'up' or 'down'")

class FeedRequest(BaseModel):
    latitude: Optional[float] = Field(None, description="Current latitude of the user")
    longitude: Optional[float] = Field(None, description="Current longitude of the user")
    radius_km: Optional[float] = Field(50.0, description="Radius in km for location-based feeds")
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


# ── Comment schemas ────────────────────────────────────────────────

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Comment text")
    parent_id: Optional[UUID] = Field(None, description="Parent comment ID for replies")
    replied_to_user_id: Optional[UUID] = Field(None, description="Target user ID if this is a reply to another user")


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, description="Updated comment text")


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    parent_id: Optional[UUID] = None
    content: str
    author: AuthorSnippet
    replied_to_user: Optional[AuthorSnippet] = None
    upvotes_count: int = 0
    downvotes_count: int = 0
    user_vote: Optional[int] = None
    replies: List["CommentResponse"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

CommentResponse.model_rebuild()  # resolve forward reference for nested replies


# ── Bookmark schemas ───────────────────────────────────────────────

class BookmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    created_at: datetime


class BookmarkToggleResponse(BaseModel):
    bookmarked: bool
    message: str
