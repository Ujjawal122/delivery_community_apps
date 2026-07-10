from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class CommunityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    about: Optional[str] = Field(None, description="About the community")
    purpose: str = Field("other", description="Purpose: education, fun, technology, etc.")
    is_public: bool = Field(True, description="Public or Private community")

class CommunityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    unique_name: str
    about: Optional[str] = None
    purpose: str
    is_public: bool
    created_by: Optional[UUID] = None
    created_at: datetime


class JoinRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    community_id: UUID
    user_id: UUID
    status: str
    created_at: datetime


class CommunityMembershipStatus(BaseModel):
    is_member: bool
    role: Optional[str] = None
    join_request_status: Optional[str] = None
