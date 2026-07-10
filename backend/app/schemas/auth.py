from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from uuid import UUID
from typing import Optional


MAX_BCRYPT_PASSWORD_BYTES = 72


class PasswordBytesMixin(BaseModel):
    @field_validator("password", "new_password", check_fields=False)
    @classmethod
    def validate_bcrypt_password_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
            raise ValueError("Password must be 72 bytes or fewer")
        return value


# ── Mixins ─────────────────────────────────────────────────────────

class EmailMixin(BaseModel):
    @field_validator("email", mode="before", check_fields=False)
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.lower().strip()
        return value

# ── Registration ───────────────────────────────────────────────────

class RegisterRequest(PasswordBytesMixin, EmailMixin):
    full_name: str = Field(..., min_length=1, max_length=255,
                           description="The full name of the user")
    password: str = Field(..., min_length=8, max_length=255,
                          description="Minimum 8 characters, maximum 72 bytes")
    email: EmailStr = Field(..., description="The email address of the user")
    phone_number: Optional[str] = Field(None, max_length=20,
                                        description="The phone number of the user")
    interests: Optional[list[str]] = Field(None, description="List of user interests")
    latitude: Optional[float] = Field(None, description="User's latitude")
    longitude: Optional[float] = Field(None, description="User's longitude")


# ── Login ──────────────────────────────────────────────────────────

class LoginRequest(PasswordBytesMixin, EmailMixin):
    email: EmailStr = Field(..., description="The email address of the user")
    password: str = Field(..., min_length=8, max_length=255,
                          description="Minimum 8 characters, maximum 72 bytes")
    latitude: Optional[float] = Field(None, description="Current latitude")
    longitude: Optional[float] = Field(None, description="Current longitude")


# ── Tokens ─────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Short-lived access token (JWT)")
    refresh_token: str = Field(..., description="Long-lived refresh token (JWT)")
    token_type: str = Field(default="bearer", description="Token scheme")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="The refresh token to rotate")


# ── Logout ─────────────────────────────────────────────────────────

class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., description="The refresh token to revoke")


# ── User profile ───────────────────────────────────────────────────

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="The unique identifier of the user")
    full_name: str = Field(..., description="The full name of the user")
    email: EmailStr = Field(..., description="The email address of the user")
    phone_number: Optional[str] = Field(None, description="The phone number of the user")
    avatar: Optional[str] = Field(None, description="The avatar URL of the user")
    bio: Optional[str] = Field(None, description="The bio of the user")
    company: Optional[str] = Field(None, description="The company of the user")
    vehicle_type: Optional[str] = Field(None, description="The vehicle type of the user")
    is_verified: bool = Field(..., description="Whether the user is verified")


# ── Register response ──────────────────────────────────────────────

class RegisterResponse(BaseModel):
    message: str
    user: UserResponse


# ── Generic message ────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str


# ── Forgot / Reset Password ────────────────────────────────────────

class ForgotPasswordRequest(EmailMixin):
    email: EmailStr = Field(..., description="Email address linked to your account")


class ResetPasswordRequest(PasswordBytesMixin):
    token: str = Field(..., description="Password-reset token received via email")
    new_password: str = Field(..., min_length=8, max_length=255,
                              description="Your new password (8-72 bytes)")


# ── Email verification ─────────────────────────────────────────────

class ResendVerificationRequest(EmailMixin):
    email: EmailStr = Field(..., description="Email address to resend verification to")
