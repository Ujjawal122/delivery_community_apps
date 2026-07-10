from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


# ── Read / Response ────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Full user profile returned to the client."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    vehicle_type: Optional[str] = None
    interests: Optional[list[str]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime


# ── Profile update ─────────────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    """
    PATCH /users/me — update any subset of profile fields.
    All fields are optional; omitted fields are left unchanged.
    """
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=1000)
    company: Optional[str] = Field(None, max_length=255)
    vehicle_type: Optional[str] = Field(None, max_length=255)
    interests: Optional[list[str]] = Field(None, description="List of user interests")
    latitude: Optional[float] = Field(None, description="User's latitude")
    longitude: Optional[float] = Field(None, description="User's longitude")


# ── Account settings ───────────────────────────────────────────────

class ChangeEmailRequest(BaseModel):
    """POST /users/me/change-email"""
    new_email: EmailStr = Field(..., description="The new email address")
    password: str = Field(..., description="Current password to confirm identity")


class ChangePasswordRequest(BaseModel):
    """POST /users/me/change-password"""
    current_password: str = Field(..., description="Your current password")
    new_password: str = Field(..., min_length=8, max_length=255,
                              description="New password (8–72 bytes)")

    @field_validator("new_password")
    @classmethod
    def validate_bcrypt_length(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be 72 bytes or fewer")
        return v


class DeleteAccountRequest(BaseModel):
    """DELETE /users/me — requires password confirmation."""
    password: str = Field(..., description="Current password to confirm account deletion")


# ── Avatar ─────────────────────────────────────────────────────────

class AvatarResponse(BaseModel):
    """Returned after a successful avatar upload or removal."""
    message: str
    avatar_url: Optional[str] = None


# ── Generic ────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
