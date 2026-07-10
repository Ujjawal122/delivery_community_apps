"""
routers/auth.py — Authentication endpoints.
All handlers use the standard ApiResponse envelope.
Redis is injected via Depends(get_redis).
"""

from fastapi import APIRouter, Depends, Query, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ok, created, no_data, ApiResponse
from app.dependencies import get_current_user, get_db, get_redis
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=ApiResponse, status_code=201,
             summary="Register a new user account")
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    result = await AuthService.register_user(db, redis, request)
    return created(result, result.message)


@router.post("/login", response_model=ApiResponse, summary="Login and receive tokens")
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    result = await AuthService.login_user(db, redis, request)
    return ok(result, "Login successful")


@router.post("/refresh", response_model=ApiResponse, summary="Rotate refresh token")
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    result = await AuthService.refresh_access_token(db, redis, request.refresh_token)
    return ok(result, "Token refreshed")


@router.post("/logout", response_model=ApiResponse, summary="Logout / revoke refresh token")
async def logout(
    http_request: Request,
    request: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    # Pass the current access token's JTI so it gets blacklisted immediately
    jti: str | None = getattr(http_request.state, "jti", None)
    await AuthService.logout_user(db, redis, request.refresh_token, jti)
    return no_data("Logged out successfully")


@router.get("/verify-email", response_model=ApiResponse, summary="Verify email address")
async def verify_email(
    token: str = Query(..., description="Email verification token"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    await AuthService.verify_email(db, redis, token)
    return no_data("Email verified successfully")


@router.post("/resend-verification", response_model=ApiResponse,
             summary="Resend email verification")
async def resend_verification(
    request: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    await AuthService.resend_verification_email(db, redis, request.email)
    return no_data("If this email is registered and unverified, a new link has been sent")


@router.post("/forgot-password", response_model=ApiResponse,
             summary="Request a password-reset email")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    await AuthService.forgot_password(db, redis, request.email)
    return no_data("If this email is registered, a password reset link has been sent")


@router.post("/reset-password", response_model=ApiResponse,
             summary="Reset password using token")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    await AuthService.reset_password(db, redis, request.token, request.new_password)
    return no_data("Password reset successfully. Please log in again.")


@router.get("/me", response_model=ApiResponse, summary="Get current authenticated user")
async def get_me(current_user: User = Depends(get_current_user)):
    return ok(UserResponse.model_validate(current_user), "Profile retrieved")
