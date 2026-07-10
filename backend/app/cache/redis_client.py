

from typing import Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_client: Optional[Redis] = None


def _build_client() -> Redis:
    """Build the async Redis client for Redis Cloud (TLS)."""
    if settings.REDIS_USE_TLS:
        # Redis Cloud endpoint — always TLS (rediss://)
        client = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            ssl=True,
            ssl_cert_reqs="none",   # Redis Cloud uses self-signed certs
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    else:
        # Local / docker Redis (no TLS)
        client = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    return client


async def connect() -> None:
    """Create the connection pool. Call once at app startup."""
    global _redis_client
    _redis_client = _build_client()
    # Verify connectivity immediately so startup fails fast
    pong = await _redis_client.ping()
    logger.info(
        "redis_connected",
        extra={
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "tls": settings.REDIS_USE_TLS,
            "ping": pong,
        },
    )


async def close() -> None:
    """Close the connection pool. Call once at app shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("redis_disconnected")


def get_redis_client() -> Redis:
    """
    Return the active client.
    Raises RuntimeError if called before connect().
    """
    if _redis_client is None:
        raise RuntimeError("Redis client not initialised — call connect() first")
    return _redis_client
