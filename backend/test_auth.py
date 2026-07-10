"""
test_auth.py — Full end-to-end auth flow test.
Uses a fake in-memory Redis so no real Redis Cloud connection is needed.
Each step uses its own DB session so one failure doesn't cascade.
"""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.exceptions import AppError, UnauthorizedError
from app.models import (  # noqa — registers all models
    Comment,
    CommentVote,
    Community,
    Gate,
    GateReview,
    HazardImage,
    HazardReport,
    HazardVote,
    Notification,
    Post,
    PostVote,
    RefreshToken,
    User,
)
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService
from app.services.jwt_service import JWTService
from app.services.password_service import PasswordService

engine = create_async_engine(settings.DATABASE_URL, echo=False)
Session = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

PASS = "[PASS]"
FAIL = "[FAIL]"
results: list[bool] = []


def ok(label: str, detail: str = "") -> None:
    msg = f"  {PASS} {label}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    results.append(True)


def fail(label: str, err) -> None:
    print(f"  {FAIL} {label}  ->  {err}")
    results.append(False)


def make_fake_redis() -> MagicMock:
    """
    Minimal in-memory fake Redis for testing.
    Supports: set, get, delete, exists, incr, expire, zadd, zrem,
    lpush, ltrim, lrange, llen, hset, hgetall, rpush, blpop,
    sadd, smembers, srem, zrange, zrevrange, zincrby, zcount,
    zremrangebyscore, zscore, scan_iter, info, ping.
    """
    store: dict = {}

    class FakeRedis:
        async def ping(self): return True
        async def set(self, k, v, ex=None, **kw): store[k] = v; return True
        async def get(self, k): return store.get(k)
        async def delete(self, *keys):
            for k in keys: store.pop(k, None)
        async def exists(self, k): return 1 if k in store else 0
        async def incr(self, k):
            store[k] = str(int(store.get(k, "0")) + 1); return int(store[k])
        async def expire(self, k, ttl): return True
        async def zadd(self, k, m, **kw): store.setdefault(k, {}); store[k].update(m)
        async def zrem(self, k, *m):
            for i in m: store.get(k, {}).pop(i, None)
        async def zincrby(self, k, amount, m):
            store.setdefault(k, {}); store[k][m] = store[k].get(m, 0) + amount
        async def zrevrange(self, k, s, e, withscores=False):
            items = sorted((store.get(k) or {}).items(), key=lambda x: -x[1])
            if e == -1: e = len(items) - 1
            sliced = items[s:e+1]
            return sliced if withscores else [m for m, _ in sliced]
        async def zrange(self, k, s, e, **kw):
            items = list((store.get(k) or {}).keys())
            return items[s:] if e == -1 else items[s:e+1]
        async def zcount(self, k, mn, mx): return len(store.get(k) or {})
        async def zremrangebyscore(self, k, mn, mx): pass
        async def zscore(self, k, m): return (store.get(k) or {}).get(m)
        async def lpush(self, k, *v):
            store.setdefault(k, []); [store[k].insert(0, i) for i in v]
        async def ltrim(self, k, s, e): store[k] = (store.get(k) or [])[s:e+1]
        async def lrange(self, k, s, e):
            lst = store.get(k) or []
            return lst[s:] if e == -1 else lst[s:e+1]
        async def llen(self, k): return len(store.get(k) or [])
        async def rpush(self, k, *v): store.setdefault(k, []); store[k].extend(v)
        async def blpop(self, k, timeout=0):
            lst = store.get(k) or []
            if lst: return (k, lst.pop(0))
            return None
        async def hset(self, k, mapping=None, **kw):
            store.setdefault(k, {})
            if mapping: store[k].update(mapping)
        async def hgetall(self, k): return dict(store.get(k) or {})
        async def sadd(self, k, *v): store.setdefault(k, set()); store[k].update(v)
        async def srem(self, k, *v): [store.get(k, set()).discard(i) for i in v]
        async def smembers(self, k): return set(store.get(k) or set())
        async def info(self, section=None): return {"redis_version": "fake", "connected_clients": 1}
        async def scan_iter(self, pattern="*"):
            import fnmatch
            for k in list(store.keys()):
                if fnmatch.fnmatch(k, pattern):
                    yield k
        async def aclose(self): pass

    return FakeRedis()


async def run() -> None:
    test_email = f"authtest_{uuid.uuid4().hex[:8]}@example.com"
    test_pw = "TestPass123!"
    print(f"\nTest account: {test_email}\n")

    redis = make_fake_redis()
    user_id = None
    access = None
    refresh = None

    # ── 1. Register ──────────────────────────────────────────────
    print("-- 1. Register --")
    async with Session() as db:
        try:
            from unittest.mock import patch, AsyncMock
            req = RegisterRequest(full_name="Auth Tester", email=test_email, password=test_pw)
            with patch("app.services.email_service.EmailService.send_verification_email",
                       new_callable=AsyncMock):
                resp = await AuthService.register_user(db, redis, req)
            await db.commit()
            user_id = resp.user.id
            ok("register", f"user_id={user_id}")
        except Exception as e:
            fail("register", e)
            return

    # ── 1.5 Verify Email ─────────────────────────────────────────
    print("\n-- 1.5 Verify Email --")
    async with Session() as db:
        try:
            evt = JWTService.create_email_verification_token(test_email)
            await AuthService.verify_email(db, redis, evt)
            await db.commit()
            ok("verify_email manually before login")
        except Exception as e:
            fail("verify_email manually before login", e)

    # ── 2. Login ─────────────────────────────────────────────────
    print("\n-- 2. Login --")
    async with Session() as db:
        try:
            tokens = await AuthService.login_user(
                db, redis, LoginRequest(email=test_email, password=test_pw)
            )
            await db.commit()
            access = tokens.access_token
            refresh = tokens.refresh_token
            ok("login", f"token_type={tokens.token_type}")
        except Exception as e:
            fail("login", e)
            return

    # ── 3. JWT decode ─────────────────────────────────────────────
    print("\n-- 3. JWT decode --")
    try:
        payload = JWTService.decode_token_safe(access, expected_type="access")
        assert payload and payload["sub"] == str(user_id)
        ok("decode access token", f"sub={payload['sub'][:8]}...")
    except Exception as e:
        fail("decode access token", e)

    try:
        assert JWTService.decode_token_safe(refresh, expected_type="refresh")
        ok("decode refresh token")
    except Exception as e:
        fail("decode refresh token", e)

    try:
        evt = JWTService.create_email_verification_token(test_email)
        p = JWTService.decode_token_safe(evt, expected_type="email_verify")
        assert p and p["sub"] == test_email
        ok("email_verify token round-trip")
    except Exception as e:
        fail("email_verify token", e)

    try:
        prt = JWTService.create_password_reset_token(test_email)
        p = JWTService.decode_token_safe(prt, expected_type="password_reset")
        assert p and p["sub"] == test_email
        ok("password_reset token round-trip")
    except Exception as e:
        fail("password_reset token", e)

    # ── 4. get_current_user ───────────────────────────────────────
    print("\n-- 4. get_current_user --")
    async with Session() as db:
        try:
            user = await AuthService.get_current_user(db, str(user_id))
            assert user.email == test_email
            ok("get_current_user", f"email={user.email}")
        except Exception as e:
            fail("get_current_user", e)

    # ── 5. Refresh token rotation ─────────────────────────────────
    print("\n-- 5. Refresh token rotation --")
    async with Session() as db:
        try:
            new_tokens = await AuthService.refresh_access_token(db, redis, refresh)
            await db.commit()
            refresh = new_tokens.refresh_token
            ok("refresh rotation", f"new_access={new_tokens.access_token[:20]}...")
        except Exception as e:
            fail("refresh rotation", e)

    # ── 6. Logout ─────────────────────────────────────────────────
    print("\n-- 6. Logout --")
    async with Session() as db:
        try:
            await AuthService.logout_user(db, redis, refresh)
            await db.commit()
            ok("logout — token revoked")
        except Exception as e:
            fail("logout", e)

    # ── 7. Refresh after logout must be rejected ──────────────────
    print("\n-- 7. Refresh after logout (expect rejection) --")
    async with Session() as db:
        try:
            await AuthService.refresh_access_token(db, redis, refresh)
            fail("refresh after logout", "should have raised but did not")
        except (AppError, HTTPException) as e:
            ok("refresh after logout correctly rejected", f"type={type(e).__name__}")
        except Exception as e:
            fail("refresh after logout", e)

    # ── 8. Password service ───────────────────────────────────────
    print("\n-- 8. Password service --")
    try:
        h = PasswordService.hash_password(test_pw)
        assert PasswordService.verify_password(test_pw, h)
        assert not PasswordService.verify_password("WrongPass!", h)
        ok("hash + verify correct password")
        ok("reject wrong password")
    except Exception as e:
        fail("password service", e)

    # ── 9. Token blacklist (Redis) ────────────────────────────────
    print("\n-- 9. Token blacklist (Redis) --")
    try:
        from app.cache.redis_service import TokenStore
        jti = str(uuid.uuid4())
        await TokenStore.blacklist_access_token(redis, jti)
        assert await TokenStore.is_access_token_blacklisted(redis, jti)
        ok("blacklist access token + check")
        # Non-blacklisted JTI should not be blocked
        assert not await TokenStore.is_access_token_blacklisted(redis, "other-jti")
        ok("non-blacklisted jti passes")
    except Exception as e:
        fail("token blacklist", e)

    # ── 10. Email verification (Redis single-use) ─────────────────
    print("\n-- 10. Email verification --")
    async with Session() as db:
        try:
            from unittest.mock import patch, AsyncMock
            token = JWTService.create_email_verification_token(test_email)
            with patch("app.services.email_service.EmailService.send_verification_email",
                       new_callable=AsyncMock):
                await AuthService.verify_email(db, redis, token)
            await db.commit()
            ok("verify_email")
        except Exception as e:
            fail("verify_email", e)

    async with Session() as db:
        try:
            token = JWTService.create_email_verification_token(test_email)
            with patch("app.services.email_service.EmailService.send_verification_email",
                       new_callable=AsyncMock):
                await AuthService.verify_email(db, redis, token)
            await db.commit()
            ok("verify_email (idempotent)")
        except Exception as e:
            fail("verify_email idempotent", e)

    # ── 11. Reset password ────────────────────────────────────────
    print("\n-- 11. Reset password --")
    new_pw = "NewPass456!"
    async with Session() as db:
        try:
            token = JWTService.create_password_reset_token(test_email)
            await AuthService.reset_password(db, redis, token, new_pw)
            await db.commit()
            ok("reset_password")
        except Exception as e:
            fail("reset_password", e)

    async with Session() as db:
        try:
            tokens = await AuthService.login_user(
                db, redis, LoginRequest(email=test_email, password=new_pw)
            )
            await db.commit()
            ok("login with new password after reset")
        except Exception as e:
            fail("login with new password after reset", e)

    # ── 12. Redis service smoke-tests ─────────────────────────────
    print("\n-- 12. Redis service smoke-tests --")
    try:
        from app.cache.redis_service import (
            TrendingStore, NotificationStore, JobQueue,
            SearchStore, OnlineStore, SessionStore, RateLimiter,
            UserCache, CommunityCache, FeedCache,
        )

        await TrendingStore.increment_post_score(redis, "post-1", 5)
        top = await TrendingStore.get_trending_posts(redis, 5)
        assert top[0][0] == "post-1"
        ok("trending posts sorted set")

        await NotificationStore.push(redis, str(user_id), {"type": "like", "msg": "test"})
        notifs = await NotificationStore.get_all(redis, str(user_id))
        assert len(notifs) == 1 and notifs[0]["type"] == "like"
        ok("notification push + get")

        await JobQueue.enqueue(redis, "email", {"to": "a@b.com", "subject": "hi"})
        job = await JobQueue.dequeue(redis, "email", timeout=1)
        assert job and job["to"] == "a@b.com"
        ok("job queue enqueue + dequeue")

        await SearchStore.add_suggestion(redis, "ujjawal")
        suggestions = await SearchStore.get_suggestions(redis, "ujj")
        assert "ujjawal" in suggestions
        ok("search suggestions")

        await OnlineStore.heartbeat(redis, str(user_id))
        assert await OnlineStore.is_online(redis, str(user_id))
        online = await OnlineStore.get_online_users(redis)
        assert str(user_id) in online
        ok("online presence heartbeat + check")

        sid = str(uuid.uuid4())
        await SessionStore.create(redis, sid, str(user_id), device="pytest", ip="127.0.0.1")
        sess = await SessionStore.get(redis, sid)
        assert sess and sess["user_id"] == str(user_id)
        ok("session create + get")

        count, exceeded = await RateLimiter.check(redis, "127.0.0.1", "login", limit=5)
        assert count == 1 and not exceeded
        ok("rate limiter check (under limit)")

        await UserCache.set(redis, str(user_id), {"full_name": "Test", "email": test_email})
        cached = await UserCache.get(redis, str(user_id))
        assert cached and cached["full_name"] == "Test"
        ok("user cache set + get")

        await CommunityCache.set(redis, "comm-1", {"name": "Delivery Heroes"})
        cc = await CommunityCache.get(redis, "comm-1")
        assert cc and cc["name"] == "Delivery Heroes"
        ok("community cache set + get")

        await FeedCache.set(redis, str(user_id), 1, [{"id": "p1"}, {"id": "p2"}])
        feed = await FeedCache.get(redis, str(user_id), 1)
        assert feed and len(feed) == 2
        ok("feed cache set + get")

    except Exception as e:
        fail("redis service smoke-tests", e)

    # ── 13. Cleanup ───────────────────────────────────────────────
    print("\n-- 13. Cleanup --")
    async with Session() as db:
        try:
            await db.execute(text("DELETE FROM users WHERE email = :e"), {"e": test_email})
            await db.commit()
            ok("cleanup")
        except Exception as e:
            fail("cleanup", e)

    await engine.dispose()


async def main() -> None:
    sep = "=" * 55
    print(f"\n{sep}")
    print("  Auth + Redis — End-to-End Test")
    print(sep)
    await run()
    passed = sum(results)
    total = len(results)
    print(f"\n{sep}")
    print(f"  Results: {passed}/{total} passed {'[ALL PASS]' if passed == total else '[SOME FAILED]'}")
    print(f"{sep}\n")


if __name__ == "__main__":
    asyncio.run(main())
