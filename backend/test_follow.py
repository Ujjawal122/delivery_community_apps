"""
test_follow.py — Full end-to-end follow flow test.
Tests following, unfollowing, mutual checks, counts, and search.
"""

import asyncio
import uuid
from unittest.mock import MagicMock

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import User, Follow
from app.services.auth_service import AuthService
from app.services.follow_service import FollowService
from app.schemas.auth import RegisterRequest

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
    import traceback
    print(f"  {FAIL} {label}  ->  {err}")
    traceback.print_exc()
    results.append(False)


def make_fake_redis() -> MagicMock:
    store: dict = {}

    class FakeRedis:
        async def ping(self): return True
        async def set(self, k, v, ex=None, **kw): store[k] = v; return True
        async def get(self, k): return store.get(k)
        async def zadd(self, k, m, **kw): store.setdefault(k, {}); store[k].update(m)
        async def zrevrange(self, k, s, e, withscores=False):
            items = sorted((store.get(k) or {}).items(), key=lambda x: -x[1])
            if e == -1: e = len(items) - 1
            sliced = items[s:e+1]
            return sliced if withscores else [m for m, _ in sliced]

    return FakeRedis()


async def run() -> None:
    user1_email = f"authtest_{uuid.uuid4().hex[:8]}@example.com"
    user2_email = f"authtest_{uuid.uuid4().hex[:8]}@example.com"
    test_pw = "TestPass123!"

    redis = make_fake_redis()
    user1_id = None
    user2_id = None

    print("-- 1. Register Users --")
    async with Session() as db:
        try:
            from unittest.mock import patch, AsyncMock
            with patch("app.services.email_service.EmailService.send_verification_email", new_callable=AsyncMock):
                resp1 = await AuthService.register_user(db, redis, RegisterRequest(full_name="User One", email=user1_email, password=test_pw))
                resp2 = await AuthService.register_user(db, redis, RegisterRequest(full_name="User Two", email=user2_email, password=test_pw))
            await db.commit()
            user1_id = resp1.user.id
            user2_id = resp2.user.id
            ok("register users", f"user1={user1_id}, user2={user2_id}")
        except Exception as e:
            fail("register users", e)
            return

    print("\n-- 2. Follow User --")
    async with Session() as db:
        try:
            user1 = await AuthService.get_current_user(db, str(user1_id))
            # User1 follows User2
            await FollowService.follow_user(db, user1, str(user2_id))
            await db.commit()
            
            user2 = await AuthService.get_current_user(db, str(user2_id))
            assert user2.follower_count == 1
            user1 = await AuthService.get_current_user(db, str(user1_id))
            assert user1.following_count == 1
            
            mutual = await FollowService.is_mutual_follower(db, str(user1_id), str(user2_id))
            assert not mutual
            ok("User 1 follows User 2 (not mutual)")
        except Exception as e:
            fail("Follow user", e)

    print("\n-- 3. Mutual Follow --")
    async with Session() as db:
        try:
            user2 = await AuthService.get_current_user(db, str(user2_id))
            # User2 follows User1
            await FollowService.follow_user(db, user2, str(user1_id))
            await db.commit()
            
            mutual = await FollowService.is_mutual_follower(db, str(user1_id), str(user2_id))
            assert mutual
            ok("User 2 follows User 1 (mutual follow)")
        except Exception as e:
            fail("Mutual follow", e)

    print("\n-- 4. Get Followers/Following --")
    async with Session() as db:
        try:
            user1_followers, _ = await FollowService.get_followers(db, user1_id, 10, 0, user1_id)
            assert len(user1_followers) == 1
            assert user1_followers[0]["id"] == user2_id
            assert user1_followers[0]["is_mutual"]
            
            user1_following, _ = await FollowService.get_following(db, user1_id, 10, 0, user1_id)
            assert len(user1_following) == 1
            assert user1_following[0]["id"] == user2_id
            ok("Get followers/following successfully")
        except Exception as e:
            fail("Get followers/following", e)

    print("\n-- 5. Search Users --")
    async with Session() as db:
        try:
            search_res, _ = await FollowService.search_users(db, "User Two", 10, 0, user1_id)
            assert len(search_res) == 1
            assert search_res[0]["id"] == user2_id
            assert search_res[0]["is_following"]
            assert search_res[0]["is_mutual"]
            ok("Search users")
        except Exception as e:
            fail("Search users", e)

    print("\n-- 6. Unfollow User --")
    async with Session() as db:
        try:
            user1 = await AuthService.get_current_user(db, str(user1_id))
            await FollowService.unfollow_user(db, user1, str(user2_id))
            await db.commit()
            
            mutual = await FollowService.is_mutual_follower(db, str(user1_id), str(user2_id))
            assert not mutual
            user1 = await AuthService.get_current_user(db, str(user1_id))
            assert user1.following_count == 0
            ok("User 1 unfollows User 2")
        except Exception as e:
            fail("Unfollow user", e)

    print("\n-- 7. Cleanup --")
    async with Session() as db:
        try:
            await db.execute(text("DELETE FROM follows WHERE follower_id IN (:u1, :u2) OR following_id IN (:u1, :u2)"), {"u1": str(user1_id), "u2": str(user2_id)})
            await db.execute(text("DELETE FROM users WHERE id IN (:u1, :u2)"), {"u1": str(user1_id), "u2": str(user2_id)})
            await db.commit()
            ok("cleanup")
        except Exception as e:
            fail("cleanup", e)

    await engine.dispose()


async def main() -> None:
    sep = "=" * 55
    print(f"\n{sep}")
    print("  Follow System — End-to-End Test")
    print(sep)
    await run()
    passed = sum(results)
    total = len(results)
    print(f"\n{sep}")
    print(f"  Results: {passed}/{total} passed {'[ALL PASS]' if passed == total else '[SOME FAILED]'}")
    print(f"{sep}\n")


if __name__ == "__main__":
    asyncio.run(main())
