

import json
from datetime import datetime, timezone
from typing import Any

from redis.asyncio import Redis

from app.cache import keys
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TokenStore:
    """
    Refresh tokens  → STRING  key=dc:rt:<token>   value=<user_id>
    Access blacklist→ STRING  key=dc:blacklist:access:<jti>  value=1
    """

    @staticmethod
    async def store_refresh_token(
        redis: Redis,
        token: str,
        user_id: str,
        ttl: int = settings.REDIS_REFRESH_TOKEN_TTL,
    ) -> None:
        """Cache a refresh token → user_id mapping with TTL."""
        await redis.set(keys.refresh_token(token), user_id, ex=ttl)
        logger.debug("rt_stored", extra={"user_id": user_id})

    @staticmethod
    async def get_refresh_token_user(redis: Redis, token: str) -> str | None:
        """Return the user_id for a refresh token, or None if absent/expired."""
        return await redis.get(keys.refresh_token(token))

    @staticmethod
    async def delete_refresh_token(redis: Redis, token: str) -> None:
        """Remove a refresh token (called on rotation / logout)."""
        await redis.delete(keys.refresh_token(token))

    @staticmethod
    async def blacklist_access_token(
        redis: Redis,
        jti: str,
        ttl: int = settings.REDIS_ACCESS_TOKEN_BLACKLIST_TTL,
    ) -> None:
       
        await redis.set(keys.access_token_blacklist(jti), "1", ex=ttl)
        logger.debug("access_token_blacklisted", extra={"jti": jti})

    @staticmethod
    async def is_access_token_blacklisted(redis: Redis, jti: str) -> bool:
        """Return True if the access token has been blacklisted."""
        return await redis.exists(keys.access_token_blacklist(jti)) == 1



class EmailVerifyStore:
   

    @staticmethod
    async def store(
        redis: Redis,
        token: str,
        email: str,
        ttl: int = settings.REDIS_EMAIL_VERIFY_TTL,
    ) -> None:
        await redis.set(keys.email_verify_token(token), email, ex=ttl)

    @staticmethod
    async def get_email(redis: Redis, token: str) -> str | None:
        return await redis.get(keys.email_verify_token(token))

    @staticmethod
    async def consume(redis: Redis, token: str) -> str | None:
        """Get the email and atomically delete the key (single-use)."""
        key = keys.email_verify_token(token)
        email = await redis.get(key)
        if email:
            await redis.delete(key)
        return email



class PasswordResetStore:
    """
    key = dc:pwd_reset:<token>   value = <email>
    Deleted on use so a reset link works exactly once.
    """

    @staticmethod
    async def store(
        redis: Redis,
        token: str,
        email: str,
        ttl: int = settings.REDIS_PASSWORD_RESET_TTL,
    ) -> None:
        await redis.set(keys.password_reset_token(token), email, ex=ttl)

    @staticmethod
    async def consume(redis: Redis, token: str) -> str | None:
        """Get the email and atomically delete the key (single-use)."""
        key = keys.password_reset_token(token)
        email = await redis.get(key)
        if email:
            await redis.delete(key)
        return email



class UserCache:
    """
    key = dc:cache:user:<user_id>
    Stores every serialisable field of the user profile as a Redis HASH.
    Invalidated on any profile / email / password change.
    """

    @staticmethod
    async def set(
        redis: Redis,
        user_id: str,
        data: dict[str, Any],
        ttl: int = settings.REDIS_USER_CACHE_TTL,
    ) -> None:
        key = keys.user_cache(user_id)
        # HASH values must be strings
        str_data = {k: json.dumps(v) if not isinstance(v, str) else v
                    for k, v in data.items() if v is not None}
        await redis.hset(key, mapping=str_data)
        await redis.expire(key, ttl)

    @staticmethod
    async def get(redis: Redis, user_id: str) -> dict[str, Any] | None:
        key = keys.user_cache(user_id)
        data = await redis.hgetall(key)
        if not data:
            return None
        # Attempt JSON decode for non-string fields
        result: dict[str, Any] = {}
        for k, v in data.items():
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                result[k] = v
        return result

    @staticmethod
    async def invalidate(redis: Redis, user_id: str) -> None:
        await redis.delete(keys.user_cache(user_id))
        logger.debug("user_cache_invalidated", extra={"user_id": user_id})



class CommunityCache:
    """
    key = dc:cache:community:<community_id>
    Same pattern as UserCache but for community objects.
    """

    @staticmethod
    async def set(
        redis: Redis,
        community_id: str,
        data: dict[str, Any],
        ttl: int = settings.REDIS_COMMUNITY_CACHE_TTL,
    ) -> None:
        key = keys.community_cache(community_id)
        str_data = {k: json.dumps(v) if not isinstance(v, str) else v
                    for k, v in data.items() if v is not None}
        await redis.hset(key, mapping=str_data)
        await redis.expire(key, ttl)

    @staticmethod
    async def get(redis: Redis, community_id: str) -> dict[str, Any] | None:
        key = keys.community_cache(community_id)
        data = await redis.hgetall(key)
        if not data:
            return None
        result: dict[str, Any] = {}
        for k, v in data.items():
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                result[k] = v
        return result

    @staticmethod
    async def invalidate(redis: Redis, community_id: str) -> None:
        await redis.delete(keys.community_cache(community_id))




class FeedCache:
    """
    key = dc:cache:feed:<user_id>:<page>   value = JSON array of posts
    Short TTL (2 min) — feeds change frequently.
    """

    @staticmethod
    async def set(
        redis: Redis,
        user_id: str,
        page: int,
        posts: list[Any],
        ttl: int = settings.REDIS_FEED_CACHE_TTL,
    ) -> None:
        await redis.set(
            keys.feed_cache(user_id, page),
            json.dumps(posts, default=str),
            ex=ttl,
        )

    @staticmethod
    async def get(
        redis: Redis, user_id: str, page: int
    ) -> list[Any] | None:
        raw = await redis.get(keys.feed_cache(user_id, page))
        if raw is None:
            return None
        return json.loads(raw)

    @staticmethod
    async def invalidate_user(redis: Redis, user_id: str) -> None:
        """Delete all cached feed pages for a user."""
        pattern = f"dc:cache:feed:{user_id}:*"
        async for key in redis.scan_iter(pattern):
            await redis.delete(key)



class TrendingStore:
   


    @staticmethod
    async def increment_post_score(
        redis: Redis, post_id: str, increment: float = 1.0
    ) -> None:
        """Atomically bump the engagement score for a post."""
        await redis.zincrby(keys.trending_posts(), increment, post_id)
        await redis.expire(keys.trending_posts(), settings.REDIS_TRENDING_TTL)

    @staticmethod
    async def get_trending_posts(
        redis: Redis, limit: int = 20
    ) -> list[tuple[str, float]]:
        """Return top posts as [(post_id, score), ...] descending."""
        results = await redis.zrevrange(
            keys.trending_posts(), 0, limit - 1, withscores=True
        )
        return [(member, score) for member, score in results]

    @staticmethod
    async def remove_post(redis: Redis, post_id: str) -> None:
        await redis.zrem(keys.trending_posts(), post_id)

    # ── Communities ────────────────────────────────────────────────

    @staticmethod
    async def increment_community_score(
        redis: Redis, community_id: str, increment: float = 1.0
    ) -> None:
        await redis.zincrby(keys.trending_communities(), increment, community_id)
        await redis.expire(keys.trending_communities(), settings.REDIS_TRENDING_TTL)

    @staticmethod
    async def get_trending_communities(
        redis: Redis, limit: int = 10
    ) -> list[tuple[str, float]]:
        results = await redis.zrevrange(
            keys.trending_communities(), 0, limit - 1, withscores=True
        )
        return [(member, score) for member, score in results]

    @staticmethod
    async def remove_community(redis: Redis, community_id: str) -> None:
        await redis.zrem(keys.trending_communities(), community_id)



class NotificationStore:
    """
    key = dc:notifications:<user_id>
    Each element is a JSON string.  Trimmed to last MAX_NOTIFICATIONS on push.
    No TTL — notifications persist until explicitly cleared.
    """

    MAX_NOTIFICATIONS = 100

    @staticmethod
    async def push(
        redis: Redis,
        user_id: str,
        notification: dict[str, Any],
    ) -> None:
        """Prepend a notification and trim to MAX_NOTIFICATIONS."""
        key = keys.user_notifications(user_id)
        await redis.lpush(key, json.dumps(notification, default=str))
        await redis.ltrim(key, 0, NotificationStore.MAX_NOTIFICATIONS - 1)

    @staticmethod
    async def get_all(
        redis: Redis, user_id: str
    ) -> list[dict[str, Any]]:
        """Return all notifications newest-first."""
        key = keys.user_notifications(user_id)
        raw_list = await redis.lrange(key, 0, -1)
        return [json.loads(item) for item in raw_list]

    @staticmethod
    async def get_unread_count(redis: Redis, user_id: str) -> int:
        return await redis.llen(keys.user_notifications(user_id))

    @staticmethod
    async def clear(redis: Redis, user_id: str) -> None:
        await redis.delete(keys.user_notifications(user_id))


class JobQueue:
    """
    key = dc:jobs:<queue_name>
    Producer: enqueue()    → RPUSH (append to tail)
    Consumer: dequeue()    → BLPOP (block-pop from head, non-async workers)
              peek()       → LRANGE (inspect without consuming)
    """

    @staticmethod
    async def enqueue(
        redis: Redis,
        queue_name: str,
        payload: dict[str, Any],
    ) -> None:
        """Add a job to the queue."""
        await redis.rpush(
            keys.job_queue(queue_name),
            json.dumps(payload, default=str),
        )
        logger.debug("job_enqueued", extra={"queue": queue_name})

    @staticmethod
    async def dequeue(
        redis: Redis,
        queue_name: str,
        timeout: int = 0,
    ) -> dict[str, Any] | None:
        """
        Pop from the head. timeout=0 blocks indefinitely.
        Returns the job payload dict or None on timeout.
        """
        result = await redis.blpop(keys.job_queue(queue_name), timeout=timeout)
        if result is None:
            return None
        _, raw = result
        return json.loads(raw)

    @staticmethod
    async def peek(
        redis: Redis,
        queue_name: str,
        count: int = 10,
    ) -> list[dict[str, Any]]:
        """Inspect the next N jobs without consuming them."""
        raw_list = await redis.lrange(keys.job_queue(queue_name), 0, count - 1)
        return [json.loads(item) for item in raw_list]

    @staticmethod
    async def queue_length(redis: Redis, queue_name: str) -> int:
        return await redis.llen(keys.job_queue(queue_name))




class SearchStore:
    """
    key = dc:search:suggest:<first3chars>
    Members are full tokens (usernames, community names, tags).
    Searching: get all members of the matching prefix set, filter client-side
    or use a sorted set with lex range for pure-Redis prefix search.
    """

    @staticmethod
    async def add_suggestion(
        redis: Redis,
        term: str,
    ) -> None:
        """Index a term so it appears in prefix suggestions."""
        if len(term) < 1:
            return
        key = keys.search_suggestions(term)
        await redis.sadd(key, term.lower())

    @staticmethod
    async def add_suggestions(redis: Redis, terms: list[str]) -> None:
        """Batch-index multiple terms."""
        for term in terms:
            await SearchStore.add_suggestion(redis, term)

    @staticmethod
    async def get_suggestions(
        redis: Redis,
        prefix: str,
        limit: int = 10,
    ) -> list[str]:
        """
        Return up to `limit` suggestions matching the prefix.
        All members in the prefix-bucket are fetched, then filtered.
        """
        if len(prefix) < 1:
            return []
        key = keys.search_suggestions(prefix)
        members = await redis.smembers(key)
        # Filter: keep only members that actually start with prefix
        lower = prefix.lower()
        matches = [m for m in members if m.startswith(lower)]
        return matches[:limit]

    @staticmethod
    async def remove_suggestion(redis: Redis, term: str) -> None:
        key = keys.search_suggestions(term)
        await redis.srem(key, term.lower())



class OnlineStore:
   

    @staticmethod
    async def heartbeat(redis: Redis, user_id: str) -> None:
        """Mark a user as online. Call on every authenticated request."""
        now = datetime.now(timezone.utc).timestamp()
        await redis.zadd(keys.online_users(), {user_id: now})

    @staticmethod
    async def mark_offline(redis: Redis, user_id: str) -> None:
        """Explicitly remove a user (on logout)."""
        await redis.zrem(keys.online_users(), user_id)

    @staticmethod
    async def get_online_users(redis: Redis) -> list[str]:
        """
        Return all users seen within the last ONLINE_TTL seconds.
        Also prunes stale entries in the same call.
        """
        cutoff = datetime.now(timezone.utc).timestamp() - settings.REDIS_ONLINE_TTL
        # Remove stale first
        await redis.zremrangebyscore(keys.online_users(), "-inf", cutoff)
        return await redis.zrange(keys.online_users(), 0, -1)

    @staticmethod
    async def is_online(redis: Redis, user_id: str) -> bool:
        score = await redis.zscore(keys.online_users(), user_id)
        if score is None:
            return False
        cutoff = datetime.now(timezone.utc).timestamp() - settings.REDIS_ONLINE_TTL
        return score > cutoff

    @staticmethod
    async def online_count(redis: Redis) -> int:
        cutoff = datetime.now(timezone.utc).timestamp() - settings.REDIS_ONLINE_TTL
        return await redis.zcount(keys.online_users(), cutoff, "+inf")




class SessionStore:


    @staticmethod
    async def create(
        redis: Redis,
        session_id: str,
        user_id: str,
        device: str = "unknown",
        ip: str = "unknown",
    ) -> None:
        """Create a session and register it in the user's session index."""
        session_key = keys.user_session(session_id)
        index_key = keys.user_session_index(user_id)
        now = datetime.now(timezone.utc).isoformat()

        await redis.hset(session_key, mapping={
            "user_id": user_id,
            "device": device,
            "ip": ip,
            "created_at": now,
        })
        await redis.expire(session_key, settings.REDIS_SESSION_TTL)

        await redis.sadd(index_key, session_id)
        await redis.expire(index_key, settings.REDIS_SESSION_TTL)

        logger.debug("session_created", extra={
            "session_id": session_id, "user_id": user_id, "device": device
        })

    @staticmethod
    async def get(
        redis: Redis, session_id: str
    ) -> dict[str, str] | None:
        data = await redis.hgetall(keys.user_session(session_id))
        return data if data else None

    @staticmethod
    async def refresh(redis: Redis, session_id: str, user_id: str) -> None:
        """Reset TTL on active session (called on each request)."""
        await redis.expire(keys.user_session(session_id), settings.REDIS_SESSION_TTL)
        await redis.expire(keys.user_session_index(user_id), settings.REDIS_SESSION_TTL)

    @staticmethod
    async def delete(redis: Redis, session_id: str, user_id: str) -> None:
        """Delete a single session."""
        await redis.delete(keys.user_session(session_id))
        await redis.srem(keys.user_session_index(user_id), session_id)

    @staticmethod
    async def delete_all_for_user(redis: Redis, user_id: str) -> None:
        """Invalidate every session for a user (logout-all / password change)."""
        index_key = keys.user_session_index(user_id)
        session_ids = await redis.smembers(index_key)
        for sid in session_ids:
            await redis.delete(keys.user_session(sid))
        await redis.delete(index_key)
        logger.info("all_sessions_deleted", extra={"user_id": user_id})

    @staticmethod
    async def list_user_sessions(
        redis: Redis, user_id: str
    ) -> list[dict[str, str]]:
        """Return metadata for all active sessions of a user."""
        index_key = keys.user_session_index(user_id)
        session_ids = await redis.smembers(index_key)
        sessions = []
        for sid in session_ids:
            data = await redis.hgetall(keys.user_session(sid))
            if data:
                data["session_id"] = sid
                sessions.append(data)
        return sessions


class RateLimiter:
   

    @staticmethod
    async def check(
        redis: Redis,
        identifier: str,
        action: str,
        limit: int,
        window: int = settings.REDIS_RATE_LIMIT_TTL,
    ) -> tuple[int, bool]:
       
        key = keys.rate_limit(identifier, action)
        count = await redis.incr(key)
        if count == 1:
            # First hit — set expiry
            await redis.expire(key, window)
        exceeded = count > limit
        if exceeded:
            logger.warning(
                "rate_limit_exceeded",
                extra={"identifier": identifier, "action": action, "count": count},
            )
        return count, exceeded

    @staticmethod
    async def reset(redis: Redis, identifier: str, action: str) -> None:
        """Manually clear a rate-limit key (e.g. after successful login)."""
        await redis.delete(keys.rate_limit(identifier, action))

    @staticmethod
    async def get_count(redis: Redis, identifier: str, action: str) -> int:
        """Peek at the current count without incrementing."""
        val = await redis.get(keys.rate_limit(identifier, action))
        return int(val) if val else 0
