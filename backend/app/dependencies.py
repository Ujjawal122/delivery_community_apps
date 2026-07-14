

import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import get_redis_client
from app.cache.redis_service import OnlineStore, TokenStore
from db.session import get_db
from app.models.user import User
from app.services.jwt_service import JWTService

__all__ = ["get_db", "get_redis", "get_current_user", "get_current_user_optional"]

_bearer_scheme = HTTPBearer(auto_error=True)
_optional_bearer_scheme = HTTPBearer(auto_error=False)


# ── Redis dependency ───────────────────────────────────────────────

def get_redis() -> Redis:
    """Return the shared async Redis client (connected at startup)."""
    return get_redis_client()


# ── Auth dependency ────────────────────────────────────────────────

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
   
    token = credentials.credentials
    payload = JWTService.decode_token_safe(token, expected_type="access")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Blacklist check (Redis — O(1)) ─────────────────────────────
    jti: str | None = payload.get("jti")
    if jti and await TokenStore.is_access_token_blacklisted(redis, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        uid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token: invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── DB lookup ──────────────────────────────────────────────────
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Online heartbeat (best-effort — never fail request) ────────
    try:
        await OnlineStore.heartbeat(redis, str(user.id))
    except Exception:
        pass

    # Attach jti to request state so routers can pass it to logout/change-password
    request.state.jti = jti

    return user

async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User | None:
    if not credentials:
        return None
    try:
        return await get_current_user(request, credentials, db, redis)
    except HTTPException:
        return None
