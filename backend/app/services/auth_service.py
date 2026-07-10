

import uuid
from datetime import datetime, timezone, timedelta

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_service import (
    TokenStore,
    EmailVerifyStore,
    PasswordResetStore,
    SessionStore,
)
from app.config import settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    UnauthorizedError,
    NotFoundError,
)
from app.core.logging import get_logger
from app.models.user import User
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
)
from app.services.email_service import EmailService
from app.services.jwt_service import JWTService
from app.services.password_service import PasswordService

logger = get_logger(__name__)


class AuthService:

    # ── Register ───────────────────────────────────────────────────

    @staticmethod
    async def register_user(
        db: AsyncSession,
        redis: Redis,
        request: RegisterRequest,
    ) -> RegisterResponse:
        user_repo = UserRepository(db)

        if await user_repo.get_by_email(request.email):
            raise ConflictError("Email already registered")

        hashed = PasswordService.hash_password(request.password)
        user = await user_repo.create(
            full_name=request.full_name,
            email=request.email,
            hashed_password=hashed,
            phone_number=request.phone_number,
        )

        logger.info("user_registered", extra={"user_id": str(user.id)})

        # Store single-use verification token in Redis + send email
        try:
            token = JWTService.create_email_verification_token(user.email)
            await EmailVerifyStore.store(redis, token, user.email)
            await EmailService.send_verification_email(user.email, token)
        except Exception as exc:
            logger.warning("verification_email_failed",
                           extra={"user_id": str(user.id), "error": str(exc)})

        return RegisterResponse(
            message="Registered successfully. Check your email to verify your account.",
            user=UserResponse.model_validate(user),
        )

    # ── Login ──────────────────────────────────────────────────────

    @staticmethod
    async def login_user(
        db: AsyncSession,
        redis: Redis,
        request: LoginRequest,
    ) -> TokenResponse:
        user_repo = UserRepository(db)
        token_repo = TokenRepository(db)

        user = await user_repo.get_by_email(request.email)
        if not user or not PasswordService.verify_password(request.password, user.password):
            raise UnauthorizedError("Invalid email or password")

        # if not user.is_verified:
        #     raise ForbiddenError("Please verify your email before logging in")

        access_token = JWTService.create_access_token(user.id)
        refresh_token_str = JWTService.create_refresh_token(user.id)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        # Persist to Postgres (source of truth) + Redis (fast path)
        await token_repo.create(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=expires_at,
        )
        await TokenStore.store_refresh_token(redis, refresh_token_str, str(user.id))

        logger.info("user_logged_in", extra={"user_id": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
        )

    # ── Refresh Token ──────────────────────────────────────────────

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        redis: Redis,
        refresh_token_str: str,
    ) -> TokenResponse:
        token_repo = TokenRepository(db)

        # 1. Verify JWT signature + type
        payload = JWTService.decode_token_safe(refresh_token_str, expected_type="refresh")
        if not payload:
            raise UnauthorizedError("Invalid or expired refresh token")

        # 2. Redis fast path — is the token still live?
        cached_user_id = await TokenStore.get_refresh_token_user(redis, refresh_token_str)
        if cached_user_id is None:
            # Not in Redis — check Postgres (handles edge case of Redis eviction)
            db_token = await token_repo.get_by_token(refresh_token_str)
            if db_token is None or db_token.is_revoked:
                raise UnauthorizedError("Refresh token has been revoked or does not exist")
            now = datetime.now(timezone.utc)
            exp = db_token.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp <= now:
                raise UnauthorizedError("Refresh token has expired")
            user_id = uuid.UUID(str(db_token.user_id))
        else:
            user_id = uuid.UUID(cached_user_id)

        # 3. Revoke old token everywhere
        await TokenStore.delete_refresh_token(redis, refresh_token_str)
        db_token = await token_repo.get_by_token(refresh_token_str)
        if db_token:
            await token_repo.revoke(db_token)

        # 4. Issue new tokens
        now = datetime.now(timezone.utc)
        new_access = JWTService.create_access_token(user_id)
        new_refresh_str = JWTService.create_refresh_token(user_id)
        new_expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await token_repo.create(
            user_id=user_id,
            token=new_refresh_str,
            expires_at=new_expires,
        )
        await TokenStore.store_refresh_token(redis, new_refresh_str, str(user_id))

        logger.info("token_rotated", extra={"user_id": str(user_id)})

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh_str,
            token_type="bearer",
        )

    # ── Logout ─────────────────────────────────────────────────────

    @staticmethod
    async def logout_user(
        db: AsyncSession,
        redis: Redis,
        refresh_token_str: str,
        access_token_jti: str | None = None,
    ) -> None:
       
        token_repo = TokenRepository(db)

        # Remove RT from Redis
        await TokenStore.delete_refresh_token(redis, refresh_token_str)

        # Revoke RT in Postgres
        db_token = await token_repo.get_by_token(refresh_token_str)
        if db_token and not db_token.is_revoked:
            await token_repo.revoke(db_token)
            logger.info("user_logged_out",
                        extra={"user_id": str(db_token.user_id)})

        # Blacklist the access token so it cannot be reused
        if access_token_jti:
            await TokenStore.blacklist_access_token(redis, access_token_jti)

    # ── Email Verification ─────────────────────────────────────────

    @staticmethod
    async def verify_email(
        db: AsyncSession,
        redis: Redis,
        token: str,
    ) -> None:
      
        user_repo = UserRepository(db)

        # Single-use consume from Redis
        email_from_redis = await EmailVerifyStore.consume(redis, token)

        # Also validate the JWT itself
        payload = JWTService.decode_token_safe(token, expected_type="email_verify")
        if not payload:
            raise BadRequestError("Invalid or expired verification token")

        email: str = payload.get("sub") or email_from_redis or ""
        if not email:
            raise BadRequestError("Invalid verification token")

        user = await user_repo.get_by_email(email)
        if user is None:
            raise NotFoundError("User not found")
        if user.is_verified:
            return  # idempotent

        user.is_verified = True
        await db.flush()
        logger.info("email_verified", extra={"user_id": str(user.id)})

    # ── Resend Verification ────────────────────────────────────────

    @staticmethod
    async def resend_verification_email(
        db: AsyncSession,
        redis: Redis,
        email: str,
    ) -> None:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(email)
        if user and not user.is_verified:
            token = JWTService.create_email_verification_token(user.email)
            try:
                await EmailVerifyStore.store(redis, token, user.email)
                await EmailService.send_verification_email(user.email, token)
                logger.info("verification_email_resent",
                            extra={"user_id": str(user.id)})
            except Exception as exc:
                logger.warning("verification_email_resend_failed",
                               extra={"user_id": str(user.id), "error": str(exc)})

    # ── Forgot Password ────────────────────────────────────────────

    @staticmethod
    async def forgot_password(
        db: AsyncSession,
        redis: Redis,
        email: str,
    ) -> None:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(email)
        if user:
            token = JWTService.create_password_reset_token(user.email)
            try:
                await PasswordResetStore.store(redis, token, user.email)
                await EmailService.send_password_reset_email(user.email, token)
                logger.info("password_reset_email_sent",
                            extra={"user_id": str(user.id)})
            except Exception as exc:
                logger.warning("password_reset_email_failed",
                               extra={"user_id": str(user.id), "error": str(exc)})

    # ── Reset Password ─────────────────────────────────────────────

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        redis: Redis,
        token: str,
        new_password: str,
    ) -> None:
        """
        Consume the single-use reset token from Redis, then update password
        and revoke all refresh tokens (Postgres + Redis).
        """
        user_repo = UserRepository(db)
        token_repo = TokenRepository(db)

        # Single-use consume
        email_from_redis = await PasswordResetStore.consume(redis, token)

        # Validate JWT
        payload = JWTService.decode_token_safe(token, expected_type="password_reset")
        if not payload:
            raise BadRequestError("Invalid or expired password-reset token")

        email: str = payload.get("sub") or email_from_redis or ""
        if not email:
            raise BadRequestError("Invalid password-reset token")

        user = await user_repo.get_by_email(email)
        if not user:
            raise BadRequestError("Invalid or expired password-reset token")

        user.password = PasswordService.hash_password(new_password)

        # Revoke all Postgres refresh tokens
        await token_repo.revoke_all_for_user(user.id)
        await db.flush()

        # Delete all Redis refresh token keys for this user
        # (pattern scan — acceptable because password reset is rare)
        await _purge_user_refresh_tokens_from_redis(redis, str(user.id))

        # Clear all sessions
        await SessionStore.delete_all_for_user(redis, str(user.id))

        logger.info("password_reset", extra={"user_id": str(user.id)})

    # ── Get Current User ───────────────────────────────────────────

    @staticmethod
    async def get_current_user(db: AsyncSession, user_id: str) -> User:
        user_repo = UserRepository(db)
        try:
            uid = uuid.UUID(user_id)
        except (ValueError, AttributeError):
            raise UnauthorizedError("Invalid user ID in token")
        user = await user_repo.get_by_id(uid)
        if user is None:
            raise NotFoundError("User not found")
        return user


# ── Private helper ─────────────────────────────────────────────────

async def _purge_user_refresh_tokens_from_redis(
    redis: Redis, user_id: str
) -> None:
    
    pattern = "dc:rt:*"
    async for key in redis.scan_iter(pattern):
        val = await redis.get(key)
        if val == user_id:
            await redis.delete(key)
