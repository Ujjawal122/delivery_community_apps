from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

# Search User Response Item
class UserSearchItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    username: Optional[str] = None
    email: EmailStr
    avatar: Optional[str] = None
    follower_count: int
    following_count: int
    
    # Follow status related to current user
    is_following: bool = False
    is_followed_by: bool = False
    is_mutual: bool = False


# Pagination Response for Search
class UserSearchResponse(BaseModel):
    items: List[UserSearchItem]
    total: int
    limit: int
    offset: int


# Simple message response for follow/unfollow actions
class FollowActionResponse(BaseModel):
    message: str
    follower_count: int
    following_count: int
