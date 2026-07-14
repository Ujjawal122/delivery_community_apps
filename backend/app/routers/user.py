"""
routers/user.py — User management endpoints.
Redis injected via Depends(get_redis).
JTI from request.state passed to password/delete operations.
"""

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ApiResponse, no_data, ok
from app.dependencies import get_current_user, get_db, get_redis
from app.models.user import User
from app.schemas.user import (
    ChangeEmailRequest,
    ChangePasswordRequest,
    DeleteAccountRequest,
    UpdateProfileRequest,
    UserResponse,
)
from app.schemas.follow import UserSearchResponse, FollowActionResponse, UserSearchItem
from app.services.user_service import UserService
from app.services.follow_service import FollowService
import uuid

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=ApiResponse, summary="Get current user profile")
async def get_profile(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Cache-aside: served from Redis HASH when warm. 🔐 Bearer token required."""
    data = await UserService.get_profile(db, redis, current_user)
    # data is already a dict — wrap in UserResponse for schema validation
    return ok(UserResponse.model_validate(data), "Profile retrieved")


@router.patch("/me", response_model=ApiResponse, summary="Update profile")
async def update_profile(
    data: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Partial update. Cache invalidated on write. 🔐 Bearer token required."""
    user = await UserService.update_profile(db, redis, current_user, data)
    await db.commit()
    return ok(UserResponse.model_validate(user), "Profile updated")


@router.post("/me/avatar", response_model=ApiResponse, summary="Upload avatar image")
async def upload_avatar(
    file: UploadFile = File(..., description="jpeg/png/webp/gif, max 5 MB"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Uploads to Cloudinary, stores URL in DB, invalidates user cache. 🔐"""
    url = await UserService.upload_avatar(db, redis, current_user, file)
    await db.commit()
    return ok({"avatar_url": url}, "Avatar uploaded successfully")


@router.delete("/me/avatar", response_model=ApiResponse, summary="Remove avatar image")
async def delete_avatar(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Deletes from Cloudinary + DB + invalidates cache. 🔐"""
    await UserService.delete_avatar(db, redis, current_user)
    await db.commit()
    return no_data("Avatar removed successfully")


@router.post("/me/change-email", response_model=ApiResponse, summary="Change email address")
async def change_email(
    data: ChangeEmailRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Requires current password. Invalidates cache + kills all sessions. 🔐"""
    user = await UserService.change_email(db, redis, current_user, data)
    await db.commit()
    return ok(UserResponse.model_validate(user), "Email changed. Please verify your new address.")


@router.post("/me/change-password", response_model=ApiResponse, summary="Change password")
async def change_password(
    http_request: Request,
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Revokes all refresh tokens + blacklists current access token. 🔐"""
    jti: str | None = getattr(http_request.state, "jti", None)
    await UserService.change_password(db, redis, current_user, data, jti)
    await db.commit()
    return no_data("Password changed successfully. Please log in again.")


@router.delete("/me", response_model=ApiResponse, summary="Delete account permanently")
async def delete_account(
    http_request: Request,
    data: DeleteAccountRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Purges account, all content, Cloudinary avatar, and all Redis data. 🔐 Irreversible."""
    jti: str | None = getattr(http_request.state, "jti", None)
    await UserService.delete_account(db, redis, current_user, data.password, jti)
    await db.commit()
    return no_data("Account deleted successfully")


# ── Follow & Search Endpoints ─────────────────────────────────────

@router.get("/search", response_model=ApiResponse, summary="Search users")
async def search_users(
    q: str,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search for users by email, username, or full name."""
    items, total = await FollowService.search_users(db, q, limit, offset, current_user.id)
    response_data = UserSearchResponse(items=items, total=total, limit=limit, offset=offset)
    return ok(response_data.model_dump(), "Users retrieved")


@router.get("/suggestions", response_model=ApiResponse, summary="Get user suggestions")
async def get_suggestions(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user suggestions to follow."""
    items = await FollowService.get_suggestions(db, current_user.id, limit)
    # Reusing search response structure for simplicity
    response_data = UserSearchResponse(items=items, total=len(items), limit=limit, offset=0)
    return ok(response_data.model_dump(), "Suggestions retrieved")


@router.get("/{user_id}/followers", response_model=ApiResponse, summary="Get followers")
async def get_followers(
    user_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get followers of a specific user."""
    items, total = await FollowService.get_followers(db, user_id, limit, offset, current_user.id)
    response_data = UserSearchResponse(items=items, total=total, limit=limit, offset=offset)
    return ok(response_data.model_dump(), "Followers retrieved")


@router.get("/{user_id}/following", response_model=ApiResponse, summary="Get following")
async def get_following(
    user_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get users that a specific user is following."""
    items, total = await FollowService.get_following(db, user_id, limit, offset, current_user.id)
    response_data = UserSearchResponse(items=items, total=total, limit=limit, offset=offset)
    return ok(response_data.model_dump(), "Following retrieved")


@router.post("/{user_id}/follow", response_model=ApiResponse, summary="Follow a user")
async def follow_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Follow another user."""
    result = await FollowService.follow_user(db, current_user, user_id)
    return ok(result, result["message"])


@router.delete("/{user_id}/follow", response_model=ApiResponse, summary="Unfollow a user")
async def unfollow_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unfollow a user."""
    result = await FollowService.unfollow_user(db, current_user, user_id)
    return ok(result, result["message"])

