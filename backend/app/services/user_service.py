"""
app/services/user_service.py
User management business logic.

Redis layer:
  - get_profile    → try UserCache first, fall back to DB, then re-cache
  - update_profile → write DB, invalidate UserCache
  - upload_avatar  → write DB, invalidate UserCache
  - delete_avatar  → write DB, invalidate UserCache
  - change_email   → write DB, invalidate UserCache, purge all sessions
  - change_password→ write DB, invalidate UserCache, purge all sessions
  - delete_account → write DB, invalidate UserCache, purge all sessions
"""

from fastapi import UploadFile
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_service import UserCache, SessionStore, TokenStore
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
)
from app.core.logging import get_logger
from app.models.user import User
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import ChangeEmailRequest, ChangePasswordRequest, UpdateProfileRequest
from app.services.cloudinary_service import CloudinaryService
from app.services.password_service import PasswordService

logger = get_logger(__name__)


class UserService:

    # ── Get profile ────────────────────────────────────────────────

    @staticmethod
    async def get_profile(
        db: AsyncSession,
        redis: Redis,
        current_user: User,
    ) -> dict:
        """
        Cache-aside pattern:
          1. Try Redis HASH cache
          2. Miss → return DB model (caller serialises and re-caches)
        Returns a dict ready for UserResponse.model_validate().
        """
        user_id = str(current_user.id)
        cached = await UserCache.get(redis, user_id)
        if cached:
            logger.debug("user_cache_hit", extra={"user_id": user_id})
            return cached

        # Cache miss — build from ORM model and store
        data = _user_to_dict(current_user)
        await UserCache.set(redis, user_id, data)
        return data

    # ── Update profile ─────────────────────────────────────────────

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        redis: Redis,
        current_user: User,
        data: UpdateProfileRequest,
    ) -> User:
        updated_fields = []
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(current_user, field, value)
                updated_fields.append(field)

        if updated_fields:
            await db.flush()
            await db.refresh(current_user)
            await UserCache.invalidate(redis, str(current_user.id))
            logger.info("profile_updated", extra={
                "user_id": str(current_user.id), "fields": updated_fields
            })

        return current_user

    # ── Upload avatar ──────────────────────────────────────────────

    @staticmethod
    async def upload_avatar(
        db: AsyncSession,
        redis: Redis,
        current_user: User,
        file: UploadFile,
    ) -> str:
        url = await CloudinaryService.upload_avatar(file, str(current_user.id))
        current_user.avatar = url
        await db.flush()
        await db.refresh(current_user)
        await UserCache.invalidate(redis, str(current_user.id))
        logger.info("avatar_uploaded", extra={
            "user_id": str(current_user.id), "url": url
        })
        return url

    # ── Delete avatar ──────────────────────────────────────────────

    @staticmethod
    async def delete_avatar(
        db: AsyncSession,
        redis: Redis,
        current_user: User,
    ) -> None:
        if current_user.avatar is None:
            raise NotFoundError("No avatar to delete")

        await CloudinaryService.delete_avatar(str(current_user.id))
        current_user.avatar = None
        await db.flush()
        await UserCache.invalidate(redis, str(current_user.id))
        logger.info("avatar_deleted", extra={"user_id": str(current_user.id)})

    # ── Change email ───────────────────────────────────────────────

    @staticmethod
    async def change_email(
        db: AsyncSession,
        redis: Redis,
        current_user: User,
        data: ChangeEmailRequest,
    ) -> User:
        user_repo = UserRepository(db)

        if not PasswordService.verify_password(data.password, current_user.password):
            raise UnauthorizedError("Incorrect password")

        if await user_repo.email_taken_by_other(data.new_email, current_user.id):
            raise ConflictError("Email address is already in use")

        old_email = current_user.email
        current_user.email = data.new_email
        current_user.is_verified = False
        await db.flush()
        await db.refresh(current_user)

        # Invalidate cache + kill all sessions (new email = new identity)
        await UserCache.invalidate(redis, str(current_user.id))
        await SessionStore.delete_all_for_user(redis, str(current_user.id))

        logger.info("email_changed", extra={
            "user_id": str(current_user.id),
            "old_email": old_email,
            "new_email": current_user.email,
        })
        return current_user

    # ── Change password ────────────────────────────────────────────

    @staticmethod
    async def change_password(
        db: AsyncSession,
        redis: Redis,
        current_user: User,
        data: ChangePasswordRequest,
        access_token_jti: str | None = None,
    ) -> None:
        if not PasswordService.verify_password(data.current_password, current_user.password):
            raise UnauthorizedError("Current password is incorrect")

        if PasswordService.verify_password(data.new_password, current_user.password):
            raise BadRequestError("New password must be different from the current one")

        current_user.password = PasswordService.hash_password(data.new_password)

        # Revoke all refresh tokens in Postgres
        token_repo = TokenRepository(db)
        await token_repo.revoke_all_for_user(current_user.id)
        await db.flush()

        # Blacklist current access token + kill all sessions
        if access_token_jti:
            await TokenStore.blacklist_access_token(redis, access_token_jti)
        await SessionStore.delete_all_for_user(redis, str(current_user.id))
        await UserCache.invalidate(redis, str(current_user.id))

        logger.info("password_changed", extra={"user_id": str(current_user.id)})

    # ── Delete account ─────────────────────────────────────────────

    @staticmethod
    async def delete_account(
        db: AsyncSession,
        redis: Redis,
        current_user: User,
        password: str,
        access_token_jti: str | None = None,
    ) -> None:
        if not PasswordService.verify_password(password, current_user.password):
            raise UnauthorizedError("Incorrect password. Account not deleted")

        user_id = str(current_user.id)

        # Best-effort avatar cleanup
        if current_user.avatar:
            try:
                await CloudinaryService.delete_avatar(user_id)
            except Exception as exc:
                logger.warning("avatar_cleanup_failed",
                               extra={"user_id": user_id, "error": str(exc)})

        await db.delete(current_user)
        await db.flush()

        # Purge all Redis data for this user
        await UserCache.invalidate(redis, user_id)
        await SessionStore.delete_all_for_user(redis, user_id)
        if access_token_jti:
            await TokenStore.blacklist_access_token(redis, access_token_jti)

        logger.info("account_deleted", extra={"user_id": user_id})


# ── Private helper ─────────────────────────────────────────────────

def _user_to_dict(user: User) -> dict:
    """Convert a User ORM object to a plain dict safe for Redis HASH storage."""
    from datetime import datetime
    import uuid

    result = {}
    for col in user.__table__.columns:
        val = getattr(user, col.name)
        if val is None:
            continue
        if isinstance(val, uuid.UUID):
            result[col.name] = str(val)
        elif isinstance(val, datetime):
            result[col.name] = val.isoformat()
        elif isinstance(val, bool):
            result[col.name] = str(val)
        else:
            result[col.name] = val
    return result
