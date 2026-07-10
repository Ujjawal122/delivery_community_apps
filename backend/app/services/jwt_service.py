from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from jose import JWTError, jwt
from app.config import settings


class JWTService:
    # ── Access & Refresh tokens ────────────────────────────────────

    @staticmethod
    def create_access_token(user_id: UUID) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access",
            "jti": str(uuid4()),   # unique per token — prevents collision on rapid re-issue
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: UUID) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh",
            "jti": str(uuid4()),   # unique per token — prevents UNIQUE constraint violation
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # ── Email-verification token (24 h, stateless) ─────────────────

    @staticmethod
    def create_email_verification_token(email: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            hours=settings.EMAIL_VERIFY_TOKEN_EXPIRE_HOURS
        )
        payload = {
            "sub": email,
            "exp": expire,
            "type": "email_verify",
            "jti": str(uuid4()),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # ── Password-reset token (1 h, stateless) ──────────────────────

    @staticmethod
    def create_password_reset_token(email: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
        )
        payload = {
            "sub": email,
            "exp": expire,
            "type": "password_reset",
            "jti": str(uuid4()),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # ── Decode helpers ─────────────────────────────────────────────

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and return payload; raises JWTError on failure."""
        try:
            return jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
        except JWTError as e:
            raise e

    @staticmethod
    def decode_token_safe(token: str, expected_type: str | None = None) -> dict | None:
        """Decode token; returns None if invalid/expired.
        Optionally validates the `type` claim."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            if expected_type and payload.get("type") != expected_type:
                return None
            return payload
        except JWTError:
            return None